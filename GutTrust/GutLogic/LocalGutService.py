


from GutTrust.GutLogic.LocalGutIO import LocalGutIO
from GutTrust.GutLogic.templates import GutResponse


def LocalGutService(GutService):
    
    def __init__(self,mainPath,**kwargs):
      self.Io = LocalGutIO(mainPath)


    
    def saveFoods(self,idList,date=None) -> GutResponse:
        """Saves all foods in idList to today's record if date
        is None, or attempts to modify the record of the date specified"""
        pass

    def getJson(self) -> GutResponse:
        """retrieves the Json file from the IO layer"""
        pass

    def saveMood(self,moodTuple) -> GutResponse:
        """Given a tuple (1-7,1-7,1-7) saves the moodScore
        to the DB, where the scores are (Stomach,Skin,Body)"""
        pass

    def moodIsSaved(self) -> GutResponse:
      return self.Io.moodIsSaved()