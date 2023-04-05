from GutTrust.GutLogic.templates import GutIO
import LocalGutPreprocessing as preprocess
import numpy as np


class normalEQGutAI(object):
    def __init__(self):
      self.dataTreshold = 6
      self.confidenceTreshold = 0.3
      self.ready = False
      self.foodList = list()
      self.theta = list()
      self.dataList = None

    def registerIO(self, handler: GutIO):
        self.dataHandler = handler
        self.ready = True
    
    def train(self):
      if not (self.ready):
        return False
      dataList = self.dataHandler.returnDataset(all=True)
      self.dataList = preprocess.preprocessData(dataList,validation=False)
      """
      X = n * f
      Y = n * 3
      """
      X = dataList[1]
      Y = dataList[3]
      # pinv(X' * X)^-1 * (X' *  y)
      # (f * n * n * f) * (f * n * n * 3) = (f * f) * (f * 3) = f * 3
      self.theta = np.multiply(np.pinv(np.matmul(np.transpose(X),X)),np.matmul(np.transpose(X),Y))
    
    def accuse(self):
      correlation = preprocess.normalizeAndScale(self.theta,10)
      i = 1
      for food in correlation:
        food = [i] + food
        i = i + 1
      correlation = sorted(correlation,key=lambda x:np.sum(x[1:]))
      sumOfScore = np.sum(correlation,axis=0)[3] #sum of 4th element on matrix = sum of scores for comparison
      suspects = list()
      for food in correlation:
        if food[3] <= (sumOfScore * self.confidenceTreshold):
          suspects.append(food[0]) #add index of food to suspects
        else:
          #since the list is sorted by decending, if the current element does not meet the condition, nothing else later will.
          break
      return suspects


      #TODO Check if shapes are correct,and if accuse returns coherent results.








  