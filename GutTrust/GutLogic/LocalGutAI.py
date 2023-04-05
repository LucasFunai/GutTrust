from __future__ import annotations
import matplotlib.pyplot as plt
import numpy
import scipy
import tensorflow as tf



from tensorflow.python.ops.numpy_ops import np_config
from tensorflow.keras.losses import Loss
from tensorflow.keras.metrics import Metric
from keras import backend as k_backend

from sklearn.model_selection import train_test_split

from GutTrust.GutLogic import LocalGutPreprocessing as preprocess

import math as m




from tensorflow.python.ops.numpy_ops import np_config
np_config.enable_numpy_behavior()
"""
Objectives:
1. Create AI model that can be saved to device and reutilized.
2. Implement all interface methods
"""

CATEGORICAL_MULT = 0.3
MAX_INPUTSIZE = 50
EMBEDDING_DIM = 12
"""Max input length is 100, but max vocab length is 101, as 0 is padding. Do not forget
to add +1 to tensor shapes"""

def int_linear(x):
    #TODO: Try to understand how this workaround works...
    x_rounded_NOT_differentiable = tf.round(x)
    x_rounded_differentiable = x - tf.stop_gradient(x - x_rounded_NOT_differentiable)
    return x_rounded_differentiable

def rangeOutput(inputs):
    return (inputs * 7) - 3

def clampCategorical(categorical):
        """From a list of 3x7 matrices,
        return a list of 3x3 matrices.
        The first two, the last two, and the middle three elements
        are clamped.
        !ALL RETURNED VALUES NEEDS TO BE FLOATS. EXPECT THE LIST TO BE CONVERTED TO A TENSOR!"""
        matrices = list()
        for matrix in categorical:
            current = list()
            for mood in matrix:
                score = mood.index(1)
                score += 1
                if score > 5:
                    current.append(list((0.0,0.0,1.0)))
                elif score < 3:
                    current.append(list((1.0,0.0,0.0)))
                else:
                    current.append(list((0.0,1.0,0.0)))
            matrices.append(current)
        return matrices

class custom_categorical_hinge(Loss):

    def call(self, y_true, y_pred):

        #approximation of a round operation
        #that is differentiable:
        #y = x - sin(2*pi*x) / 2 * pi
        #if this does not make sense, check online graphs.
        #TODO:Test this mess
        y_pred = tf.convert_to_tensor(y_pred)
        y_true = tf.cast(y_true, y_pred.dtype)
        four = tf.cast(4.,y_pred.dtype)
        two = tf.cast(2.,y_pred.dtype)
        y_pred = y_pred.Sub(four)
        y_true = y_true.Sub(four)
        y_pred = y_pred.Sub(y_pred.Mul(m.pi).Mul(two)).Div(two.Mul(m.pi))
        y_true = y_true.Sub(y_true.Mul(m.pi).Mul(two)).Div(two.Mul(m.pi))
        pos = tf.reduce_sum(y_true * y_pred, axis=-1)
        neg = tf.reduce_max((1. - y_true) * y_pred, axis=-1)
        zero = tf.cast(0., y_pred.dtype)
        return tf.maximum(neg - pos + 1., zero)



def forgivingAccuracy(y_true, y_pred):
        """y_pred and y_true are both 2D vectors in a categorical format, with shape [BATCH_SIZE,3,7]
        Both represents 3 mood scores, that ranges from 1 to 7, but
        y_pred is a probability distribuition.
        returns the sum of probabilities guessed correctly, normalized.
        e.g. 3 is the correct score, and it predicts with 0.3 certainty, 0.3 is added.
        then the sum is divided to normalize."""
        correct = float(0)
        total = 0

        row = 0
        """Loops through all scores, adds together the chances predicted correctly.
        e.g. Correct is "Good", and AI predicted it with 60% certainty,
        0.6 is added to the "correct" variable.
        Then, it is divided by the total probability (1 * 3)."""
        for batch in y_true:
            row = 0
            for mood in batch:
                column = 0
                for score in mood:
                    #Ugly code, but what it does is slice the tensor to get index [row][column]
                    #And then access the content
                    target = tf.slice(y_pred,begin=[0,row,column],size=[1,1,1])
                    if score == float(1):
                        correct = correct + target[0]
                    column = column + 1
                row = row + 1
                total = total + 1
        return correct / total

"""Expects input with 100 len, and with no more than 100 foods in vocabulary."""
class LocalGutAI(object):
    def __init__(self):
        self.aiModel = None
        self.dataTreshold = 6
        self.confidenceTreshold = 0.2
        self.foodList = list()
        self.createModel()
        self.ready = True
        self.confident = False

    def setListeners(self,listenerList):
        if type(listenerList) is not list:
            listenerList = [listenerList]
        self.listeners = listenerList

    def callListeners(self,functionName,argTuple=None,oneResponse=False,critical=False):
        """Calls listener.functionName(argTuple...) for
        every listener that has that function.
        if oneResponse is True, only waits for one to return and
        returns its response. if not, returns a tuple with all responses.
        returns empty list if no object responds."""
        responses = list()
        #Bypass ifstatement if oneResponse is false
        responseFlag = 0 if oneResponse else 2
        for listener in self.listeners:
            attribute = getattr(listener,functionName,None)
            if not attribute: continue
            if callable(attribute):
                response = attribute(*argTuple) if argTuple else attribute()
                if response:
                    if responseFlag == 1:
                        raise RuntimeError("""
                            More than 1 listener responded to oneResponse function:\n
                            {func}""".format(functionName))
                    responses.append(response)
                    responseFlag += 1
        try:
            return responses[0] if oneResponse else responses
        except Exception as e:
            if critical:
                raise e



    


        

    def createModel(self):

        inputLayer = tf.keras.layers.InputLayer(input_shape=(MAX_INPUTSIZE,),
                                    name="foodInput")
        
        embeddingLayer = tf.keras.layers.Embedding(MAX_INPUTSIZE + 1,EMBEDDING_DIM,mask_zero=True,
            input_length=MAX_INPUTSIZE)
        #Output is 3D,shape(1,50,12)
        #TODO: Fix overfitting.
        flattenLayer = tf.keras.layers.Flatten()
        #Output is 1D,shape(1,600)
        hiddenLayer2 = tf.keras.layers.Dense(MAX_INPUTSIZE,
                                           activation='relu',name="foodWeights")
        outputLayer = tf.keras.layers.Dense(3, activation='linear')
        model = tf.keras.Sequential()
        model.add(inputLayer)
        model.add(embeddingLayer)
        model.add(flattenLayer)
        model.add(hiddenLayer2)
        model.add(outputLayer)
        
        self.aiModel = model
        #TODO: fix garbage model.

        self.aiModel.compile(loss=["mse",custom_categorical_hinge()],
                             metrics=[tf.keras.metrics.CosineSimilarity()],
                             optimizer="Adam",run_eagerly=True)

    def train(self) -> bool:
        """Train the AI model by feeding it the data in the parameter
            Previous AI trainings are preserved.
            A data that was already used is not to be used for training again,
            but this definition does not differentiate such data, so only recent data is to be 
            used as parameter. Returns True if success."""
        """
        1. Check if model is loaded
        2. Take all data and use it for training
        3. Return true, or false if anything throws an exception.
        """
        if (not self.ready):
            return False
        """TODO: check why these return empty lists."""
        dataList = self.callListeners("returnDataset",oneResponse=True,critical=True)
        train_set,val_set = self.preprocessData(dataList,val_rate=0.2)
        if len(train_set[0]) < 6:
            return False
        earlyStop_kb = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            min_delta=0.1,
            patience=2,
            verbose=0,
            mode='auto',
            baseline=None,
            restore_best_weights=True
        )
        history = self.aiModel.fit(train_set[0], train_set[1], epochs=10,
            validation_data=(val_set[0],val_set[1]),batch_size=1,callbacks=[earlyStop_kb])
        self.plot_loss(history)
        result = self.aiModel.evaluate(val_set[0],val_set[1])
        print("Test loss, Test cosine similarity: {data}".format(data=result))
        if result[0] > 0.7: self.confident = True
        return True

    def plot_loss(self,history):
        plt.plot(history.history['loss'], label='loss')
        plt.plot(history.history['val_loss'], label='val_loss')
        plt.ylim([0, 10])
        plt.xlabel('Epoch')
        plt.ylabel('Error [MPG]')
        plt.legend()
        plt.grid(True)

    def accuse(self,i: int,absIndex=False,**kwargs) -> list:
        """Returns (ID,rank) for the top i entries that have the lowest
            gradient when predicting sickness in the next day (Contributes the most
            to low scores),
            unless confidenceCheck() returns false.
            then it returns None."""


        """TODO: for a gradient calculation, there shouldn't be any operations
            that are not differentiable.
            This probably means that embedding and flattening is the reason for the errors.
            
            Do the flattening and embedding outside the tape's scope, then starting from
            the first dense layer, compute the gradient."""
        if self.confident == False:
            if self.confidenceCheck() == False:
                return None
        model = self.aiModel
        #List is nested to create a batch.
        one_of_every = tf.constant([[[x for x in numpy.arange(1,MAX_INPUTSIZE + 1,1)]]])
        #index goes bottom-up
        #TODO: shapes and gradients are fixed. but now we have 600 gradients to try
        #to make something out of. Using reshape, rank the highest risk foods.
        embedded = model.get_layer(index=0)(one_of_every)
        flattened = model.get_layer(index=1)(embedded)
        with tf.GradientTape() as tape:
            tape.watch(flattened)
            dense1 = model.get_layer(index=2)(flattened)
            output = model.get_layer(index=3)(dense1)
        gradient = tape.gradient(output,flattened)
        #Expect this to have same shape as the embedding layer.
        reshaped = tf.reshape(gradient,[1,MAX_INPUTSIZE,EMBEDDING_DIM])
        #Expect this to have [MAX_INPUTSIZE] as shape
        perFood = tf.reduce_sum(reshaped,2)
        #TODO: truncate non existing indexes
        lastId = self.callListeners("getLastId",oneResponse=True,critical=True)
        #TODO: Raise something more specific
        if type(lastId) != int: raise Exception()
        perFood = perFood.numpy()[0][:lastId]
        #Rank is descending = Bigger risk first rank
        ranks = scipy.stats.rankdata(perFood,method="dense")
        returnable = list()
        #TODO: Decide if "i" changes the ranks returned or the absolute length
        #of output
        getRank = lambda x: x[1]
        #This is a list with tuples containing (foodId,Rank) sorted by rank in ascending order.
        for index,rank in sorted(enumerate(ranks,start=1),key=getRank):
            if rank > i: break
            returnable.append((index,rank))
        if absIndex: return returnable[:i]
        return returnable
        

    def confidenceCheck(self, **kwargs) -> bool:
        """Test the AI against already defined data.
            if loss is higher than treshold, return False. 
            if there is less data than treshold, return False.
            return True otherwise."""
        latestDays = self.callListeners("returnLatestData",argTuple=None,oneResponse=True)
        #TODO:Error on val_rate 0.
        dataSet = self.preprocessData(latestDays,val_rate=0)
        dataSet = dataSet[0]
        loss,metric = self.aiModel.evaluate(dataSet[0],dataSet[1])
        result = True if metric >= 0.7 else False
        self.confident = result
        return result


    def probabilityToConcrete(self,predictions):
        """Taking a [3,7] shaped list, converts it to a
        [3] shaped list, where it flattens the second dimension
        by taking the highest value, and retaining only its index. (Starting from 1)
        ex. [0.3,0.2,0.1,] -> 1"""
        result = list()
        row = 0
        column = 0
        #TIL: [(object)] * i creates an i sized list filled with object.
        #2021/9/30
        for batch in predictions:
            row = 0
            buffer = [0] * 3
            for mood in batch:
                column = 0
                for score in mood:
                    # row = mood, column = score.
                    if score == max(mood):
                        buffer[row] = column + 1
                        break
                    column = column + 1
                row = row + 1
            result.append(buffer)
        return result


    def importModel(self) -> int:
        """
        Tries to import an existing model.
        Returns:
        0 if success
        1 if it does not exist
        2 if an exception was thrown.
        """
        try:
            model = self.dataHandler.returnModel()
            if (model is not None):
                self.aiModel = model
                return 0
            else:
                return 1
        except Exception:
            return 2

    def foodCount(self):
        return self.dataHandler.foodCount()

    
            


    def preprocessData(self,dataList,val_rate = None):
        """From raw data obtained from sqlite, returns ([trainX,trainY],[valX,valY])
        where:
            Every X is zero padded to have 100 length
            Every Y is mean normalized, then scaled to range 1-7
            Every X which does not have a corresponding Y with the correct date is removed
        val_rate is the percentage of the data that is randomly taken 
        and added to the validation set.
        If m < 5, or if val_rate = 0, there is no validation set."""
        #TODO: Make these work
        dataSet = preprocess.alignFoodScore(dataList)

        foodSet = [data for data in dataSet[0]]

        paddedFoodList = preprocess.padFoods((foodSet),MAX_INPUTSIZE)

        scores = dataSet[1]
        #val_rate defaults to None if 0
        val_rate = val_rate if val_rate != 0 else None
        train_foods,val_foods,train_scores,val_scores = train_test_split(paddedFoodList,scores,test_size=val_rate)

        #TIL: List comprehensions can be nested. 2021/10/13
        allScores = None
        #TIL: Ternary operators. 4/11/2022
        allScores = train_scores + val_scores if val_scores else train_scores

        trainScoreSize = len(train_scores) 
        rangedScores = preprocess.normalizeAndScale(allScores,7)

        rangedTrainScores,rangedValScores = self.splitScoresForValidation(
            rangedScores,trainScoreSize,(val_scores != None)
        )
        return ([train_foods,rangedTrainScores],[val_foods,rangedValScores])

    def splitScoresForValidation(self,scoreList,trainSize,val_exists):
        """Takes a list, and returns a tuple with them split,with len being
        (trainSize,valSize). if val_exists is false, returns (scoreList,None)"""
        if not val_exists: return (scoreList,None)
        trainScores = scoreList[:trainSize]
        valScores = scoreList[trainSize:]
        return (trainScores,valScores)



    def countFoodAmount(self, foodIds: list) -> list:
        """Takes a list of lists containing foodIds,
        and converts them to a list of the quantity of each food in said list.
        This is to remedy variable input size.
        The result is a list with the size equal to every unique food available,
        and each element corresponding to the amount of entries for the food in the same index.
        Example: [1,2,3] -> [1,1,1,0,0,0,0 ... 0]
        [1,1,3] -> [2,0,1,0,0 .... 0]"""
        resultList = list()
        lastId = self.callListeners("getLastId",oneResponse=True)

        for idList in foodIds:
            buffer = [0] * lastId
            for index,column in enumerate(buffer):
                #TODO: check if this is actually assigning.
                column = idList.count(index)
            resultList.append(buffer)
        return resultList

#This had to be declared outside the class. It cannot import self

class forgivingPrecisionMetric(Metric):
    def __init__(self,**kwargs):
        super(forgivingPrecisionMetric,self).__init__(name="forgiving_precision",
        **kwargs)
        self.currentPrecision = self.add_weight(name="currentPrecision",shape=[1],initializer="zeros")

    #TODO: fix backpropagation here
    def update_state(self, y_true, y_pred,sample_weight=None):
        """y_pred and y_true are both 2D vectors in a categorical format, with shape [BATCH_SIZE,3,7]
        Both represents 3 mood scores, that ranges from 1 to 7, but
        y_pred is a probability distribuition.
        Returns accuracy, measured loosely."""
        correct = 0.0
        false = 0.0
        input_shape = tf.shape(y_true)
        if sample_weight == None:
            sample_weight = [[0] * input_shape[1]] * input_shape[0]
        for t_batch,p_batch,weight_batch in zip(y_true,y_pred,sample_weight):
            for t_mood,p_mood,weight in zip(t_batch,p_batch,weight_batch):
                if weight == 0:
                    weight = 1
                tf.print("Current variables, True value, predicted value, weight:")
                tf.print(t_mood)
                tf.print(p_mood)
                tf.print(weight)
                t_mood = tf.math.round(t_mood)
                p_mood = tf.math.round(p_mood)
                trueIsNegative = 0 > t_mood
                predIsNegative = 0 > p_mood
                if trueIsNegative != predIsNegative:
                    if p_mood == 0:
                        correct = correct + ((1 / 3) * weight)
                        false = false + ((1 / 3) * weight)
                    else:
                        false = false + (1 * weight)
                else:
                    correct = correct + (1 * weight)
        self.currentPrecision = correct / false

    def result(self):
        return self.currentPrecision


    









                    




    






    


    

        

            




