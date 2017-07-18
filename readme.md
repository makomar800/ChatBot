# Basic ChatBot for product and plan search

## Prerequesites:

* Python 2.7
* Library **TextBlob** for NLP
* Library **prettytable** for tables output

## Capabilities and examples of functionality:
Type **exit** at any time to stop the program.

Chatbot uses simple search on keywords in user's request to detect category and product.
Each user request is parsed using **TextBlob.parse()** method, which extracts nouns and adjectives from the sentence.
Nouns then used to detect category and brands of interest.

Chatbot also uses search on n-grams to detect price range patterns (from 50$ to 60$, below 40, etc). Example:

------------------------------------------------------------------------
Bot: How can I help you?
User: give me laptops from 50$ to 65$

Bot: OK, we have the following brands:

|   |   brands  | max rent | min rent | number |
|---|-----------|----------|----------|--------|
| 0 |   apple   |  64.99   |  59.99   |   2    |
| 1 | microsoft |  59.99   |  59.99   |   1    |
| 2 |   lenovo  |  59.99   |  59.99   |   1    |

Bot: Which brand would you prefer?
User: apple would be fine

Bot: OK, we have the following options for you:


| Product Id |                 name                 | brand |  plan |
|------------|--------------------------------------|-------|-------|
|     11     | MacBook Air 11" i7 2.2 8GB RAM 512GB | apple | 64.99 |
|     10     |   MacBook 12" M-5Y31 8GB RAM 516GB   | apple | 59.99 |



Bot: Would you like to look for something else?

-----------------------------------------------------------------------

Chatbot also recognizes simple ajectives (e.g. cheap, good, inexpensive, etc) in front of nouns and sort the search results accordingly, example:

-----------------------------------------------------------------------

Bot: How can I help you?
User: do you have cheap iphones?

Bot: OK, we have the following options for you:


| Product Id |         name        | brand |  plan |
|------------|---------------------|-------|-------|
|     2      |    iPhone 7 32GB    | apple | 39.99 |
|     1      |    iPhone 7 128GB   | apple | 44.99 |
|     3      | iPhone 7 Plus 128GB | apple | 49.99 |

Bot: Would you like to look for something else?
User: yes, give me good galaxy S smartphones

Bot: OK, we have the following options for you:

| Product Id |       name      |  brand  |  plan |
|------------|-----------------|---------|-------|
|     5      | Galaxy S8+ 64GB | samsung | 49.99 |
|     4      |  Galaxy S8 64GB | samsung | 44.99 |

Bot: Would you like to look for something else?

------------------------------------------------------------------------------------------------------

## How to run

Install external libraries and type **python Bot.py** in console.
