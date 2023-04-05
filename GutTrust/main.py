from inspect import Attribute
from kivy.uix.button import Button
from GutTrust.GutLogic.LocalGutIO import LocalGutIO
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.base import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stacklayout import StackLayout
from kivy.core.window import Window
from GutTrust.GutLogic.LocalGutService import LocalGutService
from GutTrust.GutLogic.templates import GutGUI, GutIO
from GutTrust.GutLogic.LocalGutAI import LocalGutAI
from GutTrust.widgets.widgets import FoodPrompt, MealPrompt, MoodPrompt, OneOptionPopup, SettingScreen, SuccessBanner, TwoOptionPopup, AddFoodButton, RemoveFoodButton, NewFoodPrompt
import functools

import os
"""
All definitions that use a pair of a food's name and its id in the database
uses a tuple, with the id being the first element and the name being second.
(id(int),name(str))
"""


class MainLayout(GutGUI):
    """First object that is instantiated when app runs.
        responsible for bridging the input from the device to the code."""

    mainPath = os.path.dirname(__file__)
    selectedFoods = list()

    def __init__(self,layers, **kwargs):
        """Layers is a tuple, of unknown length, where each
        element is a list of 1 or more objects of the same class.
        All objects placed below another will be its listener."""
        super(MainLayout, self).__init__(**kwargs)
        self.service = LocalGutService(self.mainPath)
        self.widgetList = list()
        self.setAllListeners(layers)
        if not self.Io.moodIsSaved():
            self.moodPrompt()

    def setAllListeners(self,listenerList):
        listenerList.insert(0,self)
        #Get index of every element
        for index,_ in enumerate(listenerList):
            #Pop current one
            layer = listenerList.pop(index)
            for obj in layer:
                #Unpack all the remaining layers into a list to set Listeners.
                currentListners = list()
                for remaining in listenerList:
                    for obj in remaining:
                        currentListeners += obj
                if currentListeners:
                    obj.setListeners(currentListeners)

                
                    



    def callListeners(self,functionName,argTuple,oneResponse=False):
        """Calls listener.functionName(argTuple...) for
        every listener that has that function.
        if oneResponse is True, only waits for one to return and
        returns its response. if not, returns a tuple with all responses.
        returns empty list if no object responds."""
        responses = list()
        for listener in self.listeners:
            attribute = getattr(listener,functionName,None)
            if not attribute: continue
            if callable(attribute):
                response = attribute(*argTuple)
                if response:
                    responses.append()
                    if oneResponse:
                        break
        return responses

    def findWidget(self, name) -> Widget:
        """Attempts to find a widget inside self.widgetList
            with a matching name and returns if there is one.
            If multiple widgets have the same name, the behaivior is undefined."""
        for remaining in [x for x in self.widgetList if x[0] == name]:
            return remaining[1]

    def removeByName(self, name) -> Widget:
        """Attempts to find a widget inside self.widgetList
            with a matching name and removes it from the list if there is one, and returns it.
            If multiple widgets have the same name, the behaivior is undefined."""
        found = None
        for remaining in [x for x in self.widgetList if x[0] == name]:
            found = remaining[1]
        self.widgetList.remove((name, found))
        self.remove_widget(found)

    """MAIN MENU BUTTONS"""

    def graphTap(self):
        pass

    def moodPrompt(self):
        prompt = MoodPrompt()
        self.widgetList.append(("moodPrompt", prompt))
        self.add_widget(self.findWidget("moodPrompt"))

    def foodButtonPress(self):
        prompt = FoodPrompt()
        prompt.ids.get('foodDropDown').dismiss()
        self.widgetList.append(("foodPrompt", prompt))
        self.add_widget(prompt)
        self.createFoodButtons()

    def settingButtonPress(self):
        prompt = SettingScreen()
        self.widgetList.append(("settingScreen", prompt))
        self.add_widget(prompt)

    def mealButtonPress(self):
        prompt = MealPrompt()
        prompt.ids.get('mealDropDown').dismiss()
        self.widgetList.append(("mealPrompt", prompt))
        self.add_widget(prompt)
        self.createMealButtons()

    def testButtonPress(self):
        ready = self.startTraining()
        """TODO: make updateGraph show an alert if theres not enough data"""
        self.updateGraph()

    def customFoodPrompt(self):
        prompt = NewFoodPrompt()
        self.widgetList.append(("newFoodPrompt", prompt))
        self.add_widget(prompt)

    """GRAPH CONTROLS"""
    """FOOD SCREEN BUTTONS"""

    def foodConfirmed(self, idList):
        """Given a list of foodIds, saves them all to today's record,
        then dismisses the current food prompt and shows SuccessBanner."""
        responses = self.callCriticalMethod("saveFood",(idList,))
        if any(code == 0 for code in responses):
            self.foodSaveSuccess()
            

    def foodSaveSuccess(self):
        self.foodCancel()
        self.showSuccessBanner(
            "Food succesfully registered! Click here to undo.",
                (self.Io.rollbackCommit, self.revertPopup))

    
    def foodCancel(self):
        self.removeByName("foodPrompt")
        self.selectedFoods = list()

    """MOOD SCREEN BUTTONS"""

    def moodConfirmed(self, stomach, skin, body):
        responses = self.callCriticalMethod("saveMood",(stomach,skin,body))
        if any(code == 0 for code in responses):
            self.moodSaveSuccess()

    def moodCancel(self):
        self.removeByName("moodPrompt")

    def moodSaveSuccess(self):
        self.moodCancel()

    """MEAL SCREEN BUTTONS"""
    """TODO: Refactor code to enforce SOLID."""

    def mealConfirmed(self, listAndName):
        chosenName = listAndName[1]
        # Only returns false if entry exists.
        foodIds = listAndName[0]
        if not self.Io.addNewMeal(foodIds, chosenName, False):
            overwriteFunc = functools.partial(self.Io.addNewMeal, foodIds,
                                              chosenName, True)

            bannerFunc = functools.partial(
                self.showSuccessBanner,
                "Successfully added! Click here to undo.",
                self.Io.rollbackCommit)
            message = """There is already a meal with the same name. 
            Do you want to overwrite it?"""
            popUp = TwoOptionPopup(
                (overwriteFunc, self.mealCancel, bannerFunc), None, message)
            popUp.open()
        else:
            self.mealCancel()
            self.showSuccessBanner("Successfully added! Click here to undo.")

    def mealCancel(self):
        self.removeByName("mealPrompt")
        self.selectedFoods = list()

    def foodToMeal(self, foodString, id):
        promptObject = self.findWidget("mealPrompt")
        mealStack = promptObject.ids.get("mealStack")
        if len(self.selectedFoods) == 0:
            mealStack.remove_widget(promptObject.ids.get("mealLabelContainer"))
        mealStack.add_widget(RemoveFoodButton(id, foodString))
        self.selectedFoods.append((foodString, id))

    def removeFromMeal(self, button):
        promptObject = self.findWidget("mealPrompt")
        self.selectedFoods.remove((button.text, button.foodId))
        promptObject.ids.get("mealStack").remove_widget(button)

    """CUSTOM FOOD BUTTONS"""

    def newFoodConfirmed(self):
        foodName = self.findWidget("newFoodPrompt").ids["foodTextField"].text
        if foodName is not "":
            if self.Io.addNewFood(foodName):
                popup = OneOptionPopup(self.newFoodCancel,
                                       "Your food was succesfully added!",
                                       "Successfully added!")

                popup.open()
            else:
                popup = OneOptionPopup(None,
                                       "That food is already in the list!",
                                       "Error")
                popup.open()

    def newFoodCancel(self):
        self.removeByName("newFoodPrompt")

    """SETTING SCREEN BUTTONS"""

    def foodResetPress(self):
        popup = TwoOptionPopup(
            self.Io.resetFoodJson, None,
            """This removes all meal-sets and custom foods from the list.\nTHIS ACTION CANNOT BE UNDONE!\nDo you want to continue?"""
        )
        popup.open()

    def showDisclaimerPress(self):
        pass

    def historyResetPress(self):
        pass

    def settingCancel(self):
        self.removeByName("settingScreen")

    """AI CONTROL"""

    def startTraining(self):
        if self.Ai.train():
            probabilities = self.Ai.accuse()
            if probabilities is not None:
                self.ids.get("graphEllipse").initPieSlices(probabilities)

    """MISC"""

    def getJsonText(self, identifier):
        """Returns a String specified in the current json file, searched by the
            identifier"""
        return self.Io.getJsonText(identifier)

    def createFoodButtons(self):
        idFoodPairs = self.Io.getFoodList()
        promptObject = self.findWidget("foodPrompt")
        dropdown = promptObject.ids.get('foodDropDown')
        for pair in idFoodPairs:
            """TIL: all ids can be accessed by the first widget in the chain.
                No need to do foo.ids.get('bar').ids.get('ipsum')"""
            dropdown.add_widget(AddFoodButton(pair[1], pair[0], promptObject))

    def createMealButtons(self):
        idFoodPairs = self.Io.getFoodList()
        promptObject = self.findWidget("mealPrompt")
        dropdown = promptObject.ids.get('mealDropDown')
        for pair in idFoodPairs:
            dropdown.add_widget(AddFoodButton(pair[1], pair[0], promptObject))

    def revertPopup(self):
        popup = OneOptionPopup(None, "Succesfully reverted.", "Notice")
        popup.open()

    def showSuccessBanner(self, text, clickBind):
        """Shows a banner in the bottom of the screen with the chosen text,
        and calls clickBind when clicked, if it is supplied."""
        banner = SuccessBanner(clickBind, text, self)
        self.add_widget(banner)

    def raiseForNoResponse(self,functionName):
        """Raises an exception for when a method call does not return
        any expected responses."""
        raise AttributeError("""Fatal error: None of the
            listeners assigned to MainLayout in main.py could call {funcName}""" 
            .format(funcName=functionName))

    def raiseForListenerConflict(self,functionName,responses):
        """Raises an exception for when a method call returns too many
        responses, when only one were expected."""
        responseListString = ""
        for response in responses:
            if response.code == 0:
                responseListString += "{responder}".format(responder=response.sender.__name__())
        raise EnvironmentError("""Fatal error: Listener conflict
        when calling {funcName}. Listeners that responded: \n{responderList}""".format(
            funcName=functionName,responderList=responseListString
        ) )

    def callCriticalMethod(self,functionName,argTuple,successBind=None, \
        failBind=None,oneResponse=False):
        """Attempts to call a method for any listener to respond.
        If there is no response, either call failBind, or throw
        an exception. If there is a response, call successBind if it exists,
        then return a list of responses.
        If oneResponse is True, throws an error for conflicting listeners
        if more than one responds."""
        responses = self.callListeners(functionName,argTuple)
        if not responses:
            if failBind: failBind()
            self.raiseForNoResponse(functionName)
            return
        didHandle = [response.code == 0 for response in responses]
        if any(didHandle):
            if oneResponse and didHandle.count(True) > 1:
                if failBind: failBind()
                self.raiseForListenerConflict(functionName,responses)
                return
            if successBind: successBind()
            return responses
        if successBind: successBind()
        return responses

    def notify(self,functionName,argTuple):
        """Attempts to call a method for every listener.
        Either returns a list of responses, or None
        if no listeners respond."""
        return self.callListeners(functionName,argTuple)



class GutTrustApp(App):
    state = None
    def build(self):
        layers = [LocalGutAI(),LocalGutIO()]
        return MainLayout(layers)


if __name__ == '__main__':
    GutTrustApp().run()
