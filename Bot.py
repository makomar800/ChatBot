from textblob import TextBlob, Word
import pandas as pd
import prettytable
#from StringIO import StringIO
from io import StringIO
import sys

class Bot(object):
    """ A class for Grover ChatBot """

    def __init__(self, FileName):
        """
        Constructor for ChatBot
        :param str FileName: name of the .csv file with available products
        """

        # read data from csv file
        self._data = pd.read_csv(FileName, index_col=0)
        self._data.columns = ['name', 'brand', 'category', 'plan']

        # manually add categories
        self._categories = {'computer', 'phone', 'home', 'drone', 'clock', 'game'}

        # make all the brands lower case
        self._data['brand'] = self._data['brand'].apply(lambda x: x.lower())
        # add brands
        self._all_brands = list(self._data['brand'].unique())

        # rename categories in the data frame
        self._map = {'phone':'Phones & Tablets',
                   'computer':'Computing',
                   'game':'Gaming & VR',
                   'clock':'Wearables',
                   'home':'Smart Home',
                   'drone':'Drones'
                   }

        for m, val in self._map.items():
            self._data.loc[self._data['category']==val, 'category'] = m

        # set with quit keywords
        self._quit_words = {'bye', 'bye-bye', 'exit', 'quit', 'leave'}
        # set with greeting keywords
        self._greet_words = {'hi', 'hello'}

        # word list (TextBlob)
        self._current_input = None
        # Grammatic type of words
        self._current_type = None
        # If we said hi already
        self._greeted = False
        # If we asked about category
        self._asked_cat = False
        # If we asked about brand
        self._asked_brand = False
        # If we asked about searc htype
        self._asked_search = False
        # If we asked about products
        self._asked_prod = False
        # Current category under discussion
        self._category = None
        # Current brand under discussion
        self._brand = None
        # Current search type (category first or brand first)
        self._searchtype = None

        # keywords to replace in user input
        self._replace_dict = {'laptop': 'computer',
                              'macbook': 'apple computer',
                              'macbookpro': 'apple computer',
                              'macbook pro': 'apple computer',
                              'macbookair': 'apple computer',
                              'macbook air': 'apple computer',
                              'air': 'apple computer',
                              'pro': 'apple computer',
                              'watch': 'clock',
                              'vacuum cleaner': 'samsung home',
                              'iphone': 'apple phone',
                              'galaxy': 'samsung phone',
                              'virtual reality': 'game',
                              'vr': 'game',
                              'tablet': 'phone',
                              'gaming': 'game',
                              'bot': 'samsung home',
                              'wearable': 'clock',
                              'smartphone': 'phone'
                              }

    @property
    def current_input(self):
        return self._current_input

    @property
    def current_type(self):
        return self._current_type

    @current_input.setter
    def current_input(self, inp):

        tb = TextBlob(self._preprocess_inp(inp)).tags
        self._current_input = [self._process_word(t[0]) for t in tb]
        self._current_type =[t[1] for t in tb]

    def _process_word(self, w):
        """Lemmatize and singularize the word"""

        if w not in self._all_brands:
            w = Word(w).lemmatize()
            w = Word(w).singularize()
            w = Word(w).correct()

        return w

    def _preprocess_inp(self, inp):
        """Preprocess input string"""

        inp = inp.lower()

        # replace keywords in the string (if any)
        for word, replace in self._replace_dict.items():
            if word in inp:
                inp = inp.replace(word, replace)

        return inp

    def _check_usr_quit(self):
        """Check if the user wants to quit"""

        if any(inp in self._quit_words for inp in self.current_input):
            return True
        else:
            return False


    def _check_for_greeting(self):
        """Check if user said hello"""
        if any(inp in self._greet_words for inp in self.current_input):
            return True
        else:
            return False

    def _say_hi(self):
        """Say Hi"""
        if not self._greeted:
            print("Bot: Hi there!\n")
        else:
            print("Bot: Hello again!\n")


    def _check_for_category_keywords(self):
        """
        Check if user input contains some category keywords
        :return: 
        """

        if self.current_input is not None:
            return any(inp_word in self._categories for inp_word in self.current_input)
        else:
            return False

    def _get_category_from_input(self):
        """
        Extract one category from input
        :return: 
        """

        cats = [word for word in self.current_input if word in self._categories]
        if len(cats)>=1:
            return cats[0]
        else:
            return None

    def _check_for_brand_keywords(self):
        """
        Check if user input contains some brand keywords
        :return: 
        """

        if self.current_input is not None:
            return any(inp_word in self._all_brands for inp_word in self.current_input)
        else:
            return False

    def _get_brand_from_input(self):
        """
        Extract one brand from input
        :return: 
        """

        brands = [word for word in self.current_input if word in self._all_brands]
        if len(brands)>=1:
            return brands[0]
        else:
            return None

    def _print_table(self, table):
        """
        Print table using prettytable
        :param data: 
        :return: 
        """

        df = pd.DataFrame(table)

        output = StringIO()
        df.to_csv(output)
        output.seek(0)
        pt = prettytable.from_csv(output)

        print (pt)

    def _list_categories(self, brand=None):
        """ List available categories of the products"""


        if brand is None:
            table = {'categories':[], 'number of brands': [], 'number of products':[]}
        else:
            table = {'categories':[], 'number of products':[]}

        for cat in self._categories:

            if brand is None:
                data = self._data.loc[self._data['category']==cat, :]
                table['categories'].append(self._map[cat])
                table['number of brands'].append(len(list(data['brand'].unique())))
                table['number of products'].append(len(data))
            else:
                data = self._data.loc[(self._data['category']==cat)&(self._data['brand']==brand), :]
                if len(data):
                    table['categories'].append(self._map[cat])
                    table['number of products'].append(len(data))

        self._print_table(table)

    def _list_brands(self, category=None):
        """ List available brands of the products"""


        if category is not None:
            table = {'brands':[], 'number of products': []}
            cat_brands = list(self._data.loc[self._data['category']==category, 'brand'].unique())
        else:
            table = {'brands':[], 'number of categories': [], 'number of products': []}
            cat_brands = self._all_brands

        for brand in cat_brands:
            if category:
                data = self._data.loc[
                       (self._data['category']==category)&(self._data['brand']==brand), :]

                if len(data):
                    table['brands'].append(brand)
                    table['number of products'].append(len(data))
            else:
                data = self._data.loc[(self._data['brand']==brand), :]

                if len(data):
                    table['brands'].append(brand)
                    table['number of categories'].append(len(list(data['category'].unique())))
                    table['number of products'].append(len(data))

        self._print_table(table)

    def _list_products(self, category, brand):
        """
        List all products from category and brands
        :param str category: current category
        :param str brand: brand
        :return: 
        """

        products = self._data.loc[
            (self._data['category']==category)&(self._data['brand']==brand),
            ['name', 'brand', 'plan']]

        products.sort_values(by='plan', ascending=False, inplace=True)

        output = StringIO()
        products.to_csv(output)
        output.seek(0)
        pt = prettytable.from_csv(output)

        print (pt)

    def _check_searchtype_keywords(self):
        """Check if user would like to go after brands or caegories"""

        if self.current_input is not None:
            return any(inp_word in ('brand', 'category') for inp_word in self.current_input)
        else:
            return False

    def _get_searchtype_from_input(self):
        """Get search type"""

        if 'category' in self.current_input:
            return 'category'
        elif 'brand' in self.current_input:
            return 'brand'
        else:
            return None

    def _check_no_input(self):
        """Check if user said no"""

        if (self._current_input and
                ('no' in self._current_input or 'not' in self._current_input)):
            return True
        else:
            return False

    def _check_yes_input(self):
        """Check if user said yes"""

        if ((self._current_input) and
                ('ye' in self._current_input or 'yep' in self._current_input)):
            return True

    def _back_to_default(self):

        self._asked_cat = False
        self._asked_brand = False
        self._asked_search = False
        self._asked_prod = False
        self._category = None
        self._brand = None
        self._searchtype = None

    def start_conversation(self):

        self.current_input = input("Bot: Hi, how can I help you?\nUser: ")

        while not self._check_usr_quit():

            # check for greeting
            if self._check_for_greeting():
                self._say_hi()

            # check for No answer
            if self._check_no_input():
                if self._asked_prod or self._asked_search:
                    break
                else:
                    self._back_to_default()
            elif self._check_yes_input():
                if self._asked_prod:
                    self._back_to_default()
                if self._asked_cat or self._asked_brand or self._asked_search:
                    self._asked_cat = False
                    self._asked_brand = False
                    self._asked_search = False
                    print ("Bot: Please, specify\n")
            elif self._asked_prod:
                self._back_to_default()


            # check for category keywords in input
            if self._check_for_category_keywords():
                self._category = self._get_category_from_input()

            # check for brand keywords in input
            if self._check_for_brand_keywords():
                self._brand = self._get_brand_from_input()

            # check for "brand" and "category" keywords:
            if self._check_searchtype_keywords():
                self._searchtype = self._get_searchtype_from_input()


            # The main decision tree
            if self._category is None and self._brand is None and self._searchtype is None:

                if self._asked_search:
                    print ("Sorry, I didn't understand\n")

                print ("""Bot: Would you like to look at CATEGORIES or BRANDS?
                Please, choose or enter specific PRODUCT/BRAND NAME (like iPhone or Samsung)\n""")
                self._asked_search = True

                self._asked_cat = False
                self._asked_brand = False
                self._asked_prod = False

            elif self._category is None and self._brand is None and self._searchtype is 'category':

                if self._asked_cat:
                    print ("Sorry, I didn't understand\n")

                print ("Bot: We have the following categories for you today:\n")
                self._list_categories()
                print ("Bot: do you have a particular category in mind?\n")
                self._asked_cat= True

                self._asked_brand = False
                self._asked_search = False
                self._asked_prod = False

            elif self._category is None and self._brand is None and self._searchtype is 'brand':

                if self._asked_brand:
                    print ("Sorry, I didn't understand\n")

                print ("Bot: We have the following brands for you today:\n")
                self._list_brands()
                print ("Bot: do you have a brand in mind?\n")
                self._asked_brand= True

                self._asked_cat = False
                self._asked_search = False
                self._asked_prod = False

            elif self._category and self._brand is None:

                if self._asked_brand:
                    print ("Sorry, I didn't understand\n")

                print("Bot: The category {0} has the following brands:\n".format(self._map[self._category]))
                self._list_brands(self._category)
                print ("Bot: do you have a particular brand in mind?\n")
                self._asked_brand= True

                self._asked_cat = False
                self._asked_search = False
                self._asked_prod = False

            elif self._category is None and self._brand:

                if self._asked_cat:
                    print ("Sorry, I didn't understand\n")

                print("Bot: The brand {0} is in the following categories:\n".format(self._brand))
                self._list_categories(self._brand)
                print ("Bot: do you have a category in mind?\n")
                self._asked_cat= True

                self._asked_brand = False
                self._asked_search = False
                self._asked_prod = False

            elif self._category and self._brand:
                if self._asked_prod:
                    print ("Sorry, I didn't understand\n")

                print(
                    "Bot: Here is the list of options for brand {0} in {1}:\n".format(
                        self._brand, self._map[self._category]))
                self._list_products(self._category, self._brand)
                print("Bot: would you like to look at other products?\n")

                self._asked_prod = True

                self._asked_cat = False
                self._asked_brand = False
                self._asked_search = False

            self.current_input = input("User: ")

        print("Bot: See you later!")

if __name__ == '__main__':

    bot = Bot('data.csv')
    bot.start_conversation()








