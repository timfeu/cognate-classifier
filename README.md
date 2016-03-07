    usage: classifier.py [-h] [--output OUTPUT] [--fallback-missing-cognate]
                         [--freedict-en-de] [--freedict-de-en] [--ding]
                         input

Classifies English-German word pairs either as cognates or false friends.

positional arguments:
  input                 A list of English and German words separated by tabs.
                        The last column may contain the solutions, in which
                        case the classifier performance will be printed out as
                        well.

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        The file to write the classification result to.
                        Defaults to "classified.csv".
  --fallback-missing-cognate
                        Flag whether to fall back to cognate instead of false
                        friend if neither the English nor the German word was
                        found in the dictionary.
  --freedict-en-de      Load the FreeDict English German dictionary.
  --freedict-de-en      Load the FreeDict German English dictionary.
  --ding                Load the Ding German English dictionary.