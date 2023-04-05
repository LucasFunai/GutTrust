from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, ReferenceListProperty, StringProperty
from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics.context_instructions import Color
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
import random

graphRGB = {
    "red" : (1,0.35,0.35),
    "blue" : (0.35,0.35,1),
    "green" : (0.35,1,0.35),
    "purple" : (1,0.35,1),
    "yellow" : (1,1,0.35),
    "lightBlue" : (0.35,1,1)
}


class SuccessBanner(Widget):
    """A clickable banner that pops up from the bottom of the screen.
        pressBind binds a single, or multiple functions to be executed when clicked."""
    def __init__(self,pressBind,text,parent, **kwargs):
        super(SuccessBanner,self).__init__(**kwargs)
        button = self.ids.get("bannerButton")
        button.text = text
        button.bind(on_press=lambda e:self.funcAndDismiss(pressBind))
        self.owner = parent
        self.autoDismiss = Clock.schedule_once(lambda f:self.dismissSelf(),4)

    def funcAndDismiss(self,func):
        self.autoDismiss.cancel()
        try:
            for f in func:
                f()
        except TypeError:
            func()
        self.owner.remove_widget(self)

    def dismissSelf(self):
        self.owner.remove_widget(self)



class OneOptionPopup(Popup):
    def __init__(self,closeBind,text,title, **kwargs):
        super(OneOptionPopup,self).__init__(**kwargs)
        self.title = title
        if(closeBind):
            self.on_dismiss = closeBind            
        self.ids.get("messageLabel").text = text

class TwoOptionPopup(ModalView):
    """Shows a popup with a message, and 2 buttons Yes and No.
        yesBind and noBind is optional, but if supplied with an iterable
        with method references, it binds all of them to their respective 
        buttons.
        """
    def __init__(self,yesBind,noBind,text, **kwargs):
        super(TwoOptionPopup,self).__init__(**kwargs)
        if(yesBind):
            self.ids.get("yesButton").bind(on_press=lambda e:self.funcAndClose(yesBind))
        if(noBind):
            try:
                for func in noBind:
                    self.ids.get("noButton").bind(on_press=func)
            except TypeError:
                self.ids.get("noButton").bind(on_press=noBind)
        else:
            self.ids.get("noButton").bind(on_press=self.dismiss)
        self.ids.get("messageLabel").text = text

    def funcAndClose(self,func):
        """Just calls a function then closes this view.
            If a list of functions is supplied instead, calls them all."""
        try:
            for f in func:
                f()
        except Exception:
            func()
        self.dismiss(force=True)


class NewFoodPrompt(Widget):
    pass
        
class MealPrompt(Widget):
    """Screen for binding multiple foods to the same button as a meal."""
    foodList = list()
    def __init__(self, **kwargs):
        super(MealPrompt,self).__init__(**kwargs)
        self.mealStack = self.ids.get("mealStack")

    def addFood(self,foodString,id):
        if len(self.foodList) == 0:
            container = self.ids.get("mealLabelContainer")
            self.mealStack.remove_widget(container)
        self.foodList.append((foodString,id))
        self.mealStack.add_widget(MealRemoveButton(id,foodString,self))

    def removeFood(self,foodButton):
        foodString = foodButton.text
        id = foodButton.id
        self.foodList.remove((foodString,id))
        self.remove_widget(foodButton)
    def returnListNamePair(self) -> tuple:
        buffer = [x[1] for x in self.foodList]
        name = self.ids.get("mealName").text
        self.foodList = list()
        return (buffer,name)

class MoodPrompt(Widget):
    """Screen for user input for how they are feeling"""
    pass


class MealRemoveButton(Button):
    def __init__(self,id,name,owner,**kwargs):
        super(MealRemoveButton,self).__init__(**kwargs)
        self.text = name
        self.foodId = id
        self.owner = owner
    def on_press(self):
        self.owner.removeFood(self)

class GraphInnerCircle(Widget):
    pass

class GraphOuterCircle(Widget):
    pass


class RemoveFoodButton(Button):
    def __init__(self,id,name,owner,**kwargs):
        super(RemoveFoodButton,self).__init__(**kwargs)
        self.text = name
        self.foodId = id
        self.owner = owner
    def on_press(self):
        self.owner.removeFood(self)


class AddFoodButton(Button):
    id = 0
    def __init__(self,id,name,owner,**kwargs):
        super(AddFoodButton,self).__init__(**kwargs)
        self.text = name
        self.id = id
        self.owner = owner
    def on_press(self):
        self.owner.addFood(self.text,self.id)
    
class FoodPrompt(Widget):
    """Screen for user input for what they ate"""
    foodList = list()
    def __init__(self, **kwargs):
        super(FoodPrompt,self).__init__(**kwargs)
        self.foodStack = self.ids.get("foodStack")
    def addFood(self,foodString,id):
        if len(self.foodList) == 0:
            container = self.ids.get("foodLabelContainer")
            self.remove_widget(container)
        self.foodList.append((foodString,id))
        self.foodStack.add_widget(RemoveFoodButton(id,foodString,self))
    def removeFood(self,foodButton):
        foodString = foodButton.text
        id = foodButton.id
        self.foodList.remove((foodString,id))
        self.remove_widget(foodButton)
    def returnIdsList(self) -> list():
        buffer = [x[1] for x in self.foodList]
        self.foodList = list()
        return buffer
    
            

class SuspectGraph(RelativeLayout):
    """Big circle graph in the middle of the screen with top suspects"""
    """Contains tuples of 2 ints. [0] is the allergen, [1] is the percent."""
    suspectList = ListProperty()


class SuspectDetailScreen(Widget):
    """Screen with detailed percentages when graph is clicked"""
    def on_start(self):
        with self.canvas:
            Color(1,1,1)
            Rectangle(self.pos,self.size)
            

class FoodButton(Button):
    """Button to activate food prompt"""
    """Will be inside Relative Layout. Keep that in mind when setting size."""
    text = StringProperty("Register Food")
    def __init__(self,**kwargs): 
        super(FoodButton,self).__init__(**kwargs)

class SettingScreen(Widget):
    pass    

class MoodButton(Button):
    """Button to activate mood prompt"""
    """Will be inside Relative Layout. Keep that in mind when setting size."""
    def __init__(self,**kwargs): 
        super(MoodButton,self).__init__(**kwargs)

class SettingScreen(Widget):
    """Settings screen"""
    pass

class GraphOuterCircle(Widget):
    """Displays percentage of certainty that something is causing reactions."""
    """The contents of circleList is a tuple. 
    (foodName:str,percent:int,rgb:tuple(int,int,int)"""
    def __init__(self, **kwargs):
        super(GraphOuterCircle,self).__init__(**kwargs)
        circleList = list()
    """TODO: Finish this"""
    def initPieSlices(self,foodAndPercent):
        percentBuffer = 0
        usedIndexes = list()
        colorList = list(graphRGB.values())
        for pair in foodAndPercent:
            randIndex = random.randrange(0,len(colorList))
            currentRGB = colorList.pop(randIndex)
            slice = PieSlice(currentRGB,percentBuffer,pair[1],pair[0])
            self.add_widget(slice)

class PieSlice(Widget):
    """The widget that contains the ellipses to make the graph."""
    r = NumericProperty()
    g = NumericProperty()
    b = NumericProperty()
    percent = NumericProperty()
    angleStart = NumericProperty()
    angleEnd = NumericProperty() 
    foodName = ""
    def __init__(self,rgb,prevPercentage,percentage,foodString, **kwargs):
        super(PieSlice,self).__init__(**kwargs)
        r,g,b = rgb #TIL: Destructuring. Don't use too often
        percent = percentage
        foodName = foodString
        self.previous = prevPercentage
        angleStart = 360 * prevPercentage
        angleEnd = 360 * percentage + angleStart
    
    def currentPercentage(self):
        """Used for calculating start and end angles for the ellipse.
            Returns the start percentage to be used for the next Slice in the queue.
            Return value is previous_percentage + self.percentage"""
        return self.previous + self.percentage

class GraphInnerCircle(Widget):
    """Inner circle of suspect graph."""
    pass