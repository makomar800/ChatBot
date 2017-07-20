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
        # string with row input (lower case)
        self._raw_input = None
        # Grammatic type of words
        self._current_type = None
        # If we said hi already
        self._greeted = False
        # If we asked about category
        self._asked_cat = False
        # If we asked about brand
        self._asked_brand = False
        # If we asked about search in categories
        self._asked_prod = False
        # Ask for conversation
        self._asked_conv = True
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
                              'vacuum': 'samsung home',
                              'cleaner': 'samsung home',
                              'iphone': 'apple phone',
                              'galaxy': 'samsung phone',
                              'virtual reality': 'game',
                              'vr': 'game',
                              'tablet': 'phone',
                              'gaming': 'game',
                              'bot': 'samsung home',
                              'wearable': 'clock',
                              'smartphone': 'phone',
                              'computing': 'computer',
                              'vive': 'game htc',
                              "don't": 'do not',
                              'house': 'home',
                              'like': 'want',
                              'need': 'want',
                              'give': 'want',
                              'smart': 'home'
                              }

    @property
    def current_input(self):
        return self._current_input

    @property
    def current_type(self):
        return self._current_type

    @property
    def current_type(self):
        return self._raw_input

    @current_input.setter
    def current_input(self, inp):

        tb = TextBlob(self._preprocess_inp(inp)).tags
        self._current_input = [self._process_word(t[0]) for t in tb]
        self._current_type =[t[1] for t in tb]
        self._raw_input = inp.lower()

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

        if self.current_input is not None:
            if any(inp in self._quit_words for inp in self.current_input):
                return True

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

        words = self._analyze_sentence_structure(self.current_input)

        cats = [word for word in words if word in self._categories]
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

        words = self._analyze_sentence_structure(self.current_input)

        brands = [word for word in words if word in self._all_brands]
        if len(brands)>=1:
            return brands[0]
        else:
            return None

    def _analyze_sentence_structure(self, words):
        """
        Analyzes sentence structure and discards negated terms
        dumb approach: go through sentence,
        if see 'not', 'no', 'hate', 'dislike', 'discard', discard everything until 'but' or next 'want'-like
        verb found
        :param words: 
        :return: 
        """

        words_to_ret = []
        negs = {'no', 'not'}
        hates = {'hate', 'dislike', 'discard'}
        neg_cancellers = {'but', 'want', 'like', 'need'}
        # dumb approach: go through sentence,
        # if see 'not', 'no', 'hate', 'dislike', 'discard', discard everything until 'but' or next 'want' found
        negation = False
        for ind, w in enumerate(words):

            if not ind == len(words)-1:
                if words[ind] in negs and not words[ind+1] in hates:
                    negation = True
            if not ind == 0:
                if words[ind] in hates and not words[ind-1] in negs:
                    negation = True
                if negation and words[ind] in neg_cancellers and words[ind-1] not in negs:
                    negation = False
            else:
                if words[ind] in hates:
                    negation = True

            if not negation:
                words_to_ret.append(w)

        return words_to_ret


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

    def _get_results(self, cat=None, brand=None):
        """Get results based on category and brand"""

        if cat is not None and brand is not None:
            results = self._data.loc[(self._data['category']==cat)&(self._data['brand']==brand), :]
            if len(results):
                return results, 1, 1
            else:
                return [], 0, 0

        elif cat is not None and brand is None:
            results = self._data.loc[(self._data['category']==cat), :]
            if len(results):
                return results, \
                       1,\
                       len(list(results.loc[results['category'] == cat, 'brand'].unique()))
            else:
                return [], 0, 0

        elif cat is None and brand is not None:
            results = self._data.loc[(self._data['brand']==brand), :]
            if len(results):
                return results,\
                       len(list(results.loc[results['brand'] == brand, 'category'].unique())),\
                       1
            else:
                return [], 0, 0
        else:
            return [], 0, 0


    def _list_categories(self, results, brand=None):
        """ List available categories of the products"""


        if brand is None:
            table = {'categories':[], 'number of brands': [], 'number of products':[]}
        else:
            table = {'categories':[], 'number of products':[]}

        for cat in self._categories:

            if brand is None:
                data = results.loc[results['category']==cat, :]
                table['categories'].append(self._map[cat])
                table['number of brands'].append(len(list(data['brand'].unique())))
                table['number of products'].append(len(data))
            else:
                data = results.loc[(results['category']==cat)&(results['brand']==brand), :]
                if len(data):
                    table['categories'].append(self._map[cat])
                    table['number of products'].append(len(data))

        self._print_table(table)

    def _list_brands(self, results, category=None):
        """ List available brands of the products"""


        if category is not None:
            table = {'brands':[], 'number of products': []}
            cat_brands = list(results.loc[results['category']==category, 'brand'].unique())
        else:
            table = {'brands':[], 'number of categories': [], 'number of products': []}
            cat_brands = list(results['brand'].unique())

        for brand in cat_brands:
            if category:
                data = results.loc[
                       (results['category']==category)&(results['brand']==brand), :]

                if len(data):
                    table['brands'].append(brand)
                    table['number of products'].append(len(data))
            else:
                data = results.loc[(results['brand']==brand), :]

                if len(data):
                    table['brands'].append(brand)
                    table['number of categories'].append(len(list(data['category'].unique())))
                    table['number of products'].append(len(data))

        self._print_table(table)

    def _list_products(self, results, cat, brand):
        """
        List all products from category and brands
        :param str category: current category
        :param str brand: brand
        :return: 
        """

        products = results.loc[
            (results['category']==cat)&(results['brand']==brand),
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
                ('no' in self._current_input or 'not' in self._current_input or 'nope' in self._raw_input) and
                not (self._check_for_brand_keywords())
            ):
            return True
        else:
            return False

    def _check_yes_input(self):
        """Check if user said yes"""

        if ((self._current_input) and
                ('ye' in self._current_input or
                         'yep' in self._current_input or
                         'yeah' in self._current_input or
                     ('would' in self._current_input and 'not' not in self._current_input)
                 )
            ):
            return True

    def _back_to_default(self):

        self._asked_cat = False
        self._asked_brand = False
        self._asked_search = False
        self._asked_prod = False
        self._asked_conv = True
        self._category = None
        self._brand = None
        self._searchtype = None

    def _check_match(self, item, index):
        """Count number of matches of input with item"""

        words = self._raw_input.lower().split(' ')
        words = self._analyze_sentence_structure(words)
        wname = str(item['name']).lower().split(' ')
        pname = str(item['plan']).lower().split(' ')
        matches = [w for w in words if
                   w in wname or
                   str(index).lower()==w or
                   w in pname]
        return len(matches)

    def _ask_for_particular_item(self, results):
        """ Asks for particular item in results"""

        while len(results)>1:

            self._list_products(results, cat=self._category, brand=self._brand)

            self.current_input = input("Bot: which product would you like?\nUser: ")

            if ('else' in self._raw_input or
                        'other' in self._raw_input or
                        'none' in self._raw_input or
                        'nothing' in self._raw_input or
                        'no' in self._raw_input or
                        'nope' in self._raw_input or
                        'another' in self._raw_input or
                        'others' in self._raw_input or self._check_usr_quit()):
                return 0

            scores = {}
            max_score = 0
            for index, item in results.iterrows():
                scores[index] = self._check_match(item, index)
                if scores[index]>max_score:
                    max_score = scores[index]

            if not max_score == 0:
                indeces = []
                for index, item in results.iterrows():
                    if scores[index] == max_score:
                        indeces.append(index)

                results = results.loc[indeces, :]
            else:
                print("Bot: sorry, your request does not match our records\n")

        self._list_products(results, cat=self._category, brand=self._brand)
        print("Bot: you got it!")

        return 1

    def _ask_for_conversation(self):
        """ Ask for conversation """

        self.current_input = input("Bot: would you like to look at our products?\nUser: ")

        while not self._check_usr_quit() and not self._check_no_input():

            # check for greeting
            if self._check_for_greeting():
                self._say_hi()
                return True
            if self._check_yes_input():
                return True

            self.current_input = input("Bot: Sorry? Would you like to look at our products?\nUser: ")

        return False



    def start_conversation(self):

        print ("Bot: Welcome!\n")

        while not self._check_usr_quit():

            if self._asked_conv:
                self._back_to_default()
                if not self._ask_for_conversation():
                    break
                self._asked_conv = False

            # check for No answer
            if self._check_no_input():
                if self._asked_cat or self._asked_brand:
                    self._back_to_default()
                    if not self._ask_for_conversation():
                        break
                    self._asked_conv = False

            # check for Yes answer
            elif self._check_yes_input():

                if self._asked_cat or self._asked_brand:
                    self._asked_cat = False
                    self._asked_brand = False
                    print ("Bot: Please, specify\n")

            # check for category keywords in input
            if self._check_for_category_keywords():
                self._category = self._get_category_from_input()

            # check for brand keywords in input
            if self._check_for_brand_keywords():
                self._brand = self._get_brand_from_input()

            # check for "brand" and "category" keywords:
            if self._check_searchtype_keywords():
                self._searchtype = self._get_searchtype_from_input()

            # get search results based on category and brand
            results, ncat, nbrand = self._get_results(cat=self._category, brand=self._brand)

            # check if there is a mismatch between brand and category
            if self._category is not None and self._brand is not None and not len(results):

                if self._asked_cat:
                    print("Bot: sorry there is no category {0} for brand {1}".format(self._category, self._brand))
                    self._category = None
                    results, ncat, nbrand = self._get_results(cat=self._category, brand=self._brand)
                    self._asked_cat = False

                if self._asked_brand:
                    print("Bot: sorry there is no brand {0} in category {1}".format(self._brand, self._category))
                    self._brand = None
                    results, ncat, nbrand = self._get_results(cat=self._category, brand=self._brand)
                    self._asked_brand = False

            if ncat==1 and self._category is None:
                self._category = results.loc[results.index[0], 'category']
            if nbrand==1 and self._brand is None:
                self._brand = results.loc[results.index[0], 'brand']


            # The main decision tree
            if self._category is None and self._brand is None and self._searchtype is None:

                if self._asked_cat == True:
                    print ("Bot: sorry, there is no such a product or category\n")

                print ("""Bot: we have the following categories for you today:\n""")
                self._list_categories(self._data)
                print ("Bot: do you have a particular category in mind?\n")

                self._asked_cat = True
                self._asked_brand = False

                self._searchtype = 'category'

            elif self._category is None and self._brand is None and self._searchtype is 'category':

                if self._asked_cat == True:
                    print ("Bot: sorry, there is no such a product or category\n")

                print ("Bot: We have the following categories for you today:\n")
                self._list_categories(self._data)
                print ("Bot: do you have a particular category in mind?\n")

                self._asked_cat= True
                self._asked_brand = False

            elif self._category is None and self._brand is None and self._searchtype is 'brand':

                if self._asked_brand == True:
                    print ("Bot: sorry, there is no such a product or category\n")

                print ("Bot: We have the following brands for you today:\n")
                self._list_brands(self._data)
                print ("Bot: do you have a brand in mind?\n")
                self._asked_brand= True
                self._asked_cat = False

            elif self._category and nbrand>1:
                if self._asked_brand:
                    print ("Bot: Sorry, there is no such a brand in category {0}\n".format(self._category))

                print("Bot: The category {0} has the following brands:\n".format(self._map[self._category]))
                self._list_brands(results, self._category)
                print ("Bot: do you have a particular brand in mind?\n")

                self._asked_brand= True
                self._asked_cat = False

            elif ncat>1 and self._brand:

                if self._asked_cat:
                    print ("Bot: Sorry, there is no such a category for brand {0}\n".format(self._brand))

                print("Bot: The brand {0} is in the following categories:\n".format(self._brand))
                self._list_categories(results, self._brand)
                print ("Bot: do you have a category in mind?\n")
                self._asked_cat= True
                self._asked_brand = False

            elif ncat==1 and nbrand==1:

                print(
                    "Bot: Here is the list of options for brand {0} in {1}:\n".format(
                        self._brand, self._map[self._category])
                )

                # ask user for particular item
                self._ask_for_particular_item(results)

                self._asked_conv = True
                self._asked_cat = False
                self._asked_brand = False

            if not self._asked_conv:
                self.current_input = input("User: ")

        print("Bot: See you later!")

if __name__ == '__main__':

    bot = Bot('data.csv')
    bot.start_conversation()
