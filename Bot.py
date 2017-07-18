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

        # default sorting mode for results ('e' means expensive items first)
        self._default_mode = 'e'
        # default number of results to show
        self._default_num = 4

        # read data from csv file
        self._data = pd.read_csv(FileName, index_col=0)
        self._data.columns = ['name', 'brand', 'category', 'plan']

        # manually add categories
        self._categories = ['computer', 'phone', 'home', 'drone', 'clock', 'game']

        # rename categories in the data frame
        mapping = {'Phones & Tablets': 'phone',
                   'Computing' : 'computer',
                   'Gaming & VR': 'game',
                   'Wearables': 'clock',
                   'Smart Home' : 'home',
                   'Drones': 'drone'
                   }
        for m, val in mapping.items():
            self._data.loc[self._data['category']==m, 'category'] = val

        # make all the brands lower case
        self._data['brand'] = self._data['brand'].apply(lambda x: x.lower())

        # dictionary, which contains available brands for each category
        self._brands = dict.fromkeys(self._categories, None)
        # fill the dictionary brands
        for c in self._categories:
            self._brands[c] = list(
                map(
                    lambda x: x.lower(), list(self._data.loc[self._data['category']==c, 'brand'].unique())
                )
            )

        # the following fields describe state of conversation
        self._category = None   # category of interest
        self._brand_list = None # brands of interest
        self._price_range = [-1000, +1000] # price range

        self._stop = False # flag for continuing a conversation

        # keywords to replace in user input
        self._replace_dict = {'laptop': 'computer',
                        'macbook': 'apple computer',
                        'macbookpro': 'apple computer',
                        'watch': 'clock',
                        'vacuum cleaner': 'samsung home',
                        'iphone': 'apple phone',
                        'galaxy': 'samsung phone',
                        'virtual reality': 'game ',
                        'vr': 'game'
                        }
        # some dictionary with adjectives to check in input
        # adjective influence results of sorting
        self._adjective_dict = {'good': 'e',
                                'best': 'e',
                                'fancy': 'e',
                                'cheap' : 'c',
                                'cheapest' : 'c',
                                'non-expensive': 'c',
                                'in-expensive': 'c',
                                'inexpensive': 'c'
                                }


    def _list_brands(self, category):
        """
        List all brands that satisfy user's request
        :param category: 
        :return: number of entries in the table 
        """

        if self._brands[category] is not None:
            table = {'brands':[], 'number': [], 'max rent':[], 'min rent':[]}
            for brand in self._brands[category]:
                data = self._data.loc[
                       (self._data['category']==category)&(self._data['brand']==brand)&
                       (self._data['plan']>self._price_range[0])&
                       (self._data['plan']<self._price_range[1]), :]

                if len(data):
                    table['brands'].append(brand)
                    table['number'].append(len(data))
                    table['max rent'].append(data['plan'].max())
                    table['min rent'].append(data['plan'].min())

            df = pd.DataFrame(table)
            if len(df)>1:

                print ("\nBot: OK, we have the following brands:\n")

                output = StringIO()
                df.to_csv(output)
                output.seek(0)
                pt = prettytable.from_csv(output)

                print (pt)
            return df['brands']

        return []

    def _list_devices(self, category, brand_list):
        """
        List all devices from category with brands from brand_list
        :param str category: current category
        :param list brand_list: list of brands
        :return: 
        """

        print ("\nBot: OK, we have the following options for you:")

        for brand in brand_list:

            if brand[1] == 'd':
                if category[0][1] == 'd':
                    mode = self._default_mode
                else:
                    mode = category[0][1]
            else:
                mode = brand[1]

            products = self._data.loc[
                (self._data['category']==self._category[0][0])&(self._data['brand']==brand[0])&
                (self._data['plan']>self._price_range[0])&(self._data['plan']<self._price_range[1]),
                ['name', 'brand', 'plan']]

            if mode == 'e':
                products.sort_values(by='plan', ascending=False, inplace=True)
            else:
                products.sort_values(by='plan', ascending=True, inplace=True)


            output = StringIO()
            products.head(n=self._default_num).to_csv(output)
            output.seek(0)
            pt = prettytable.from_csv(output)

            print ("\n")
            print (pt)
        print ("\n\n")

    def _get_chunk_verbs(self, words):
        """
        The function gives chunks with verbs (for future development)
        :param words: 
        """

        chunk_verbs = []
        for w in words:
            w = w.split('/')
            if w[2] == 'B-VP':
                chunk_verbs.append(
                    [(Word(w[0]).lemmatize(), w[2])]
                )
            elif w[2] == 'I-VP':
                chunk_verbs[-1].append(
                    (Word(w[0]).lemmatize(), w[2])
                )

        ret_dict = {}
        for chunk in chunk_verbs[0:1]:
            verb = [n[0] for n in chunk if n[1] == 'B-VP'][0]
            ret_dict[verb] = [n[0] for n in chunk if not n[1] == 'B-VP']

        return ret_dict

    def _get_all_nouns(self, words):
        """
        The function returns list of pairs (noun, mode) where noun can be brand or category
        and mode denotes adjective -- expensive or cheap (for sorting)
        :param words: 
        :return: 
        """

        nouns = []
        for i, w in enumerate(words):
            # try get adjective before noun
            prev_w = None
            if not i==0:
                prev_w = words[i-1].split('/')
            w = w.split('/')
            if w[1][0:2] == 'NN': # the word is noun
                if (prev_w is not None and
                            prev_w[1][0:2] in ('JJ', 'DT')): # the word is adjective before noun
                    nouns.append(
                        (Word(w[0]).lemmatize(), self._adjective_dict.get(prev_w[0], 'd'))
                    )
                else:
                    nouns.append(
                        (Word(w[0]).lemmatize(), 'd')
                    )

        return nouns

    def _search_for_price_pattern(self, inp):
        """
        This function searches for price pattern of the form:
        'from d to d'
        'between d and d'
        'below d'
        'under d'
        'above d'
        'higher than d'
        'lower than d'
        
        :param inp: 
        :return: 
        """

        wlist = TextBlob(inp).ngrams(n=4)
        for ngram in wlist:
            if ((ngram[0] == 'from' and ngram[2] == 'to') or
                    (ngram[0] == 'between' and ngram[2] == 'and')):
                try:
                    lo = float(ngram[1].strip('$'))
                    hi = float(ngram[3].strip('$'))
                except ValueError:
                    pass
                else:
                    self._price_range = [lo, hi]

        wlist = TextBlob(inp).ngrams(n=2)
        for ngram in wlist:
            if ngram[0] == 'below' or ngram[0] == 'under':
                try:
                    hi = float(ngram[1].strip('$'))
                except ValueError:
                    pass
                else:
                    self._price_range[1]= hi
            if ngram[0] == 'above':
                try:
                    lo = float(ngram[1].strip('$'))
                except ValueError:
                    pass
                else:
                    self._price_range[0]= lo

        wlist = TextBlob(inp).ngrams(n=3)
        for ngram in wlist:
            if ngram[0] == 'higher' and ngram[1] == 'than':
                try:
                    hi = float(ngram[2].strip('$'))
                except ValueError:
                    pass
                else:
                    self._price_range[1]= hi
            if ngram[0] == 'lower' and ngram[1] == 'than':
                try:
                    lo = float(ngram[2].strip('$'))
                except ValueError:
                    pass
                else:
                    self._price_range[0]= lo

    def _process_phrase(self, phrase):
        """
        Preprocess string. Break the string into nouns and verbs for future processing.
        :param str phrase: input string
        """

        # convert the string lowercase
        phrase = phrase.lower()

        # replace keywords in the string (if any)
        for word, replace in self._replace_dict.items():
            if word in phrase:
                phrase = phrase.replace(word, replace)

        phrase = TextBlob(phrase).parse()
        words = phrase.split(' ')

        verb = self._get_chunk_verbs(words)
        nouns = self._get_all_nouns(words)

        # return
        return verb, nouns

    def _ask_for_category(self, inp=None):

        """
        Initial stage of conversation.
        Here we are trying to get a category from the user.
        And try to search for brand and price range
        """

        # get input from user
        if inp is None:
            inp = input("Bot: How can I help you?\n" + "User: ")

        # patch for exist, not the best solution
        if 'exit' in inp:
            self._stop = True
            return

        # break the phrase into nouns and verbs, lemmatize nouns
        verbs, nouns = self._process_phrase(inp)

        # detect categories, which are in the user input
        self._category = [(n, mode) for n, mode in nouns if n in self._categories]

        # try to get brand, if any
        if self._category:
            self._brand_list = [
                (n, mode) for n, mode in nouns if n in self._brands[self._category[0][0]]
            ]
            # try to get price range
            self._search_for_price_pattern(inp)
        else:
            print("\nBot: sorry there is no products that much your request\n")



    def _ask_for_brand(self):
        """
        If the user didn't specify brand in his/her first sentence,
        the bot lists all brands for chosen category
        and asks to choose one.
        """

        b = self._list_brands(self._category[0][0])

        if len(b)>1:
            print ("Bot: Which brand would you prefer?")

            inp = input("User: ")
            # patch for exist, not the best solution
            if 'exit' in inp:
                self._stop = True
                return

            verbs, nouns = self._process_phrase(inp)

            self._brand_list = [(n, mode) for n, mode in nouns if n in self._brands[self._category[0][0]]]

            # try to get price range
            self._search_for_price_pattern(inp)

            if not self._brand_list:
                print ("Bot: Sorry, we didn't find any brands that much your request\n")
        elif len(b)==1:
            self._brand_list = [(b.iloc[0], 'd')]
        else:
            print ("Sorry, there is no products in specified price range\n")
            self._ask_for_continuation()


    def _ask_for_continuation(self):
        """
        When all the oprions are listed, we are asking for continuation.
        """

        print ("Bot: Would you like to look for something else?")

        inp = input("User: ").lower()
        if 'no' in inp or 'exit' in inp:
            self._stop = True
        else:
            # switch back to default state
            self._category = None
            self._brand_list = None
            self._price_range = [-1000, +1000]

            # start new conversation
            self._ask_for_category(inp)

    def process_user_input(self):
        """
        Process user input
        """

        while not self._stop:

            # ask for category until is clear
            while not self._category and not self._stop:
                self._ask_for_category()

            # if didn't get a brand so far, try to ask about brand
            while not self._brand_list and not self._stop:
                self._ask_for_brand()


            if not self._stop:
                # list all possile options
                self._list_devices(self._category, self._brand_list)

                # ask if we are going to proceed conversation
                self._ask_for_continuation()

if __name__=='__main__':

    bot = Bot('data.csv')
    bot.process_user_input()

