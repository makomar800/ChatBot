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
        self._category = []   # category of interest
        self._brand_list = [] # brands of interest
        self._price_range = [-sys.maxsize, +sys.maxsize] # price range

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
        :return: DataFrame with brand names, and basic statistics across them
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

    def _get_products(self):
        """
        Get products that satisfy user request.
        :return: DataFrame with products
        """
        products = []
        modes = []

        for brand in self._brand_list:

            if brand[1] == 'd':
                if self._category[1] == 'd':
                    mode = self._default_mode
                else:
                    mode = self._category[1]
            else:
                mode = brand[1]

            products.append(self._data.loc[
                (self._data['category']==self._category[0])&(self._data['brand']==brand[0])&
                (self._data['plan']>self._price_range[0])&(self._data['plan']<self._price_range[1]),
                ['name', 'brand', 'plan']])

            if mode == 'e':
                products[-1].sort_values(by='plan', ascending=False, inplace=True)
            else:
                products[-1].sort_values(by='plan', ascending=True, inplace=True)

            modes.append(mode)

        return products, modes


    def _list_products(self, products, modes, ind_range):
        """
        List all devices from products (list of DataFrames) using modes (sorting)
        :param str category: current category
        :param list brand_list: list of brands
        :return: 
        """

        print ("\nBot: OK, we have the following options for you:")


        # The program is limited to only one brand
        for prod_single_brand in [products[0]]:
            output = StringIO()

            if ind_range[-1]>=len(prod_single_brand):
                ind_range = range(len(prod_single_brand))

            prod_single_brand.iloc[ind_range, :].to_csv(output)
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
                    [(w[0], w[2])]
                )
            elif w[2] == 'I-VP':
                chunk_verbs[-1].append(
                    (w[0], w[2])
                )

        ret_dict = {}
        for chunk in chunk_verbs[0:1]:
            verb = [n[0] for n in chunk if n[1] == 'B-VP'][0]
            ret_dict[verb] = [n[0] for n in chunk if not n[1] == 'B-VP']

        return ret_dict

    def _get_chunk_nouns(self, words):
        """
        The function returns list of pairs (noun, mode) where noun can be brand or category
        and mode denotes adjective -- expensive or cheap (for sorting)
        :param words: 
        :return: 
        """
        nouns = []
        for w in words:
            w = w.split('/')
            if w[2] == 'B-NP':
                nouns.append([w[0]])
            elif w[2] == 'I-NP':
                nouns[-1].append(w[0])

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

        lo = None
        hi = None
        wlist = TextBlob(inp).ngrams(n=4)
        for ngram in wlist:
            if ((ngram[0] == 'from' and ngram[2] == 'to') or
                    (ngram[0] == 'between' and ngram[2] == 'and')):
                try:
                    l = float(ngram[1].strip('$'))
                    h = float(ngram[3].strip('$'))
                except ValueError:
                    pass
                else:
                    lo = l
                    hi = h

        wlist = TextBlob(inp).ngrams(n=2)
        for ngram in wlist:
            if ngram[0] == 'below' or ngram[0] == 'under':
                try:
                    h = float(ngram[1].strip('$'))
                except ValueError:
                    pass
                else:
                    hi = h

            if ngram[0] == 'above':
                try:
                    l = float(ngram[1].strip('$'))
                except ValueError:
                    pass
                else:
                    lo = l

        wlist = TextBlob(inp).ngrams(n=3)
        for ngram in wlist:
            if ngram[0] == 'higher' and ngram[1] == 'than':
                try:
                    h = float(ngram[2].strip('$'))
                except ValueError:
                    pass
                else:
                    hi = h

            if ngram[0] == 'lower' and ngram[1] == 'than':
                try:
                    l = float(ngram[2].strip('$'))
                except ValueError:
                    pass
                else:
                    lo = l
        return lo, hi

    def _lemmatize_phrase(self, phrase):
        """
        Lemmatize all words in a phrase, return new phrase
        :param phrase: 
        :return: 
        """

        words = list(map(lambda x: Word(x), phrase.split(' ')))
        lem_words = list(map(lambda x: Word(x.lemmatize()), words))
        sing_lem_words = list(map(lambda x: x.singularize(), lem_words)) # necessary for words like "iphone"

        return ' '.join(sing_lem_words)

    def _process_phrase(self, phrase):
        """
        Process phrase. extract verbs, nouns and 
        :param phrase: 
        :return: 
        """

        # convert the phrase to lowercase string
        phrase = phrase.lower()
        # convert all words in the phrase to singular form
        phrase = self._lemmatize_phrase(phrase)

        # search for price range pattern
        (lo, hi) = self._search_for_price_pattern(phrase)

        # replace keywords in the string (if any)
        for word, replace in self._replace_dict.items():
            if word in phrase:
                phrase = phrase.replace(word, replace)

        phrase = TextBlob(phrase).parse()
        words = phrase.split(' ')

        verbs = self._get_chunk_verbs(words)
        nouns = self._get_chunk_nouns(words)

        # return
        return verbs, nouns, (lo, hi)

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

        # break the phrase into nouns and verbs
        verbs, nouns, (lo, hi) = self._process_phrase(inp)

        # detect categories, which are in the user input
        cat_n = [n for n in nouns if any(x in self._categories for x in n)]
        category = []
        if cat_n:
            categories = [c for c in cat_n[0] if c in self._categories]
            modes = [c for c in cat_n[0] if c in self._adjective_dict]

            if modes:
                category = [categories[0], self._adjective_dict.get(modes[0], 'd')]
            else:
                category = [categories[0], 'd']


        # try to get brands, if any
        brand = []
        if category:

            for chunk in nouns:
                brands = [ b for b in chunk if b in self._brands[category[0]] ]
                modes = [m for m in chunk if m in self._adjective_dict]
                if brands:
                    if modes:
                        brand.append((brands[0], self._adjective_dict[modes[0]]))
                    else:
                        brand.append((brands[0], 'd'))

            # set up price range
            if lo is not None:
                self._price_range[0] = lo
            if hi is not None:
                self._price_range[1] = hi

        else:
            print("\nBot: sorry there are no products that much your request\n")

        return category[0], [brand[0]]



    def _ask_for_brand(self):
        """
        If the user didn't specify brand in his/her first sentence,
        the bot lists all brands for chosen category
        and asks to choose one.
        """

        b = self._list_brands(self._category)

        if len(b)>1:
            print ("Bot: Which brand would you prefer?")

            inp = input("User: ")
            # patch for exist, not the best solution
            if 'exit' in inp:
                self._stop = True
                return

            verbs, nouns, (lo, hi) = self._process_phrase(inp)

            brand_list = []
            for chunk in nouns:
                brands = [ b for b in chunk if b in self._brands[self._category] ]
                modes = [m for m in chunk if m in self._adjective_dict]
                if brands:
                    if modes:
                        brand_list.append((brands[0], self._adjective_dict[modes[0]]))
                    else:
                        brand_list.append((brands[0], 'd'))

            # set up price range
            if lo is not None:
                self._price_range[0] = lo
            if hi is not None:
                self._price_range[1] = hi

            if not brand_list:
                print ("Bot: Sorry, we didn't find any brands that much your request\n")
                return []
            else:
                return [brand_list[0]]
        elif len(b)==1:
            return [(b.iloc[0], 'd')]
        else:
            print ("Sorry, there are no products in specified price range\n")
            return []

    def _ask_for_options(self, ind_range, products, modes):
        """
        When there is something else on the list, the bot asks for other options
        :return: 
        """

        if not ind_range[0] == 0:
            if modes[0] == 'e':
                inp = input("\nBot: would you like to see cheaper options?\nUser:")



    def _ask_for_continuation(self):
        """
        When all the options are listed, we are asking for continuation.
        """

        print ("Bot: Would you like to look for something else?")

        inp = input("User: ").lower()
        if 'no' in inp or 'exit' in inp:
            self._stop = True
        else:
            # switch back to default state
            self._category = []
            self._brand_list = []
            self._price_range = [-sys.maxsize, +sys.maxsize]

            # start new conversation
            self._category, self._brand_list = self._ask_for_category(inp)

    def process_user_input(self):
        """
        Process user input
        """

        while not self._stop:

            # ask for category until is clear
            while not self._category and not self._stop:
                self._category, self._brand_list = self._ask_for_category()

            # if didn't get a brand so far, try to ask about brand
            while not self._brand_list and not self._stop:
                self._brand_list = self._ask_for_brand()
                if not self._brand_list:
                    self._ask_for_continuation()


            if not self._stop:
                # list all possile options
                products, modes = self._get_products()
                self._list_products(products, modes, range(0, self._default_num))

                # ask if we are going to proceed conversation
                self._ask_for_continuation()

if __name__=='__main__':

    bot = Bot('data.csv')
    bot.process_user_input()

