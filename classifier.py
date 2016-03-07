from xml.etree import ElementTree
import argparse
import re
import io

COGNATE = 1
FALSE_FRIEND = 0

def readFreeDictDictionary(filename, invert=False):
	ns = {'TEI': 'http://www.tei-c.org/ns/1.0'}
	root = ElementTree.parse(filename).getroot()
	entries = root.findall('.//TEI:entry', ns)
	
	dictionary = set()
	leftwords = set()
	rightwords = set()
	
	for entry in entries:
		leftTag = entry.find('./TEI:form/TEI:orth', ns)
		if leftTag is None:
			continue
		left = leftTag.text.lower()
		if left.startswith("to "):
			left = left[3:]
		
		for sense in entry.findall('./TEI:sense', ns):
			for cit in sense.findall('./TEI:cit', ns):
				rightTag = cit.find('./TEI:quote', ns)
				if rightTag is None:
					continue
				right = rightTag.text.lower()
				if right.startswith("to "):
					right = right[3:]
					
				if invert:
					dictionary.add(right + "\t" + left)
					leftwords.add(right)
					rightwords.add(left)
				else:
					dictionary.add(left + "\t" + right)
					leftwords.add(left)
					rightwords.add(right)
	
	return (dictionary, leftwords, rightwords)

def readDingDictionary(filename, invert=False):
	dictionary = set()
	leftwords = set()
	rightwords = set()
	to_remove = re.compile(r'ich\/er\/sie|ist\/war|du |you |he\/she|I\/he\/she|has\/had|would |sb\.|sth\.|jdm\.|etw\.|\{.+?\}|\(.+?\)|\[.+?\]|\/[a-zA-Z0-9_\.]+?\/')
	
	f = io.open(filename, encoding='utf-8')
	for line in f:
		line = line.strip()
		if line.startswith(u"#") or not line:
			continue
		
		parts = line.split(u"::")
		assert len(parts) == 2, line
		left_words = parts[0].split(u'|')
		right_words = parts[1].split(u'|')
		assert len(left_words) == len(right_words), line
		for i in range(0, len(left_words)):
			left_words[i] = to_remove.sub('', left_words[i])
			right_words[i] = to_remove.sub('', right_words[i])
			for left_word in left_words[i].split(';'):
				for right_word in right_words[i].split(';'):
					left_word = left_word.lower().strip()
					if left_word.startswith(u'to '):
						left_word = left_word[3:]
					right_word = right_word.lower().strip()
					if right_word.startswith(u'to '):
						right_word = right_word[3:]
					
					if invert:
						leftwords.add(right_word)
						rightwords.add(left_word)
						dictionary.add(right_word + "\t" + left_word)
					else:
						leftwords.add(left_word)
						rightwords.add(right_word)
						dictionary.add(left_word + "\t" + right_word)
	
	return (dictionary, leftwords, rightwords)

parser = argparse.ArgumentParser(description="Classifies English-German word pairs either as cognates or false friends.")
parser.add_argument('input', action='store', help='A list of English and German words separated by tabs. The last column may contain the solutions, in which case the classifier performance will be printed out as well.')
parser.add_argument('--output', '-o', action='store', help='The file to write the classification result to. Defaults to "classified.csv".', default='classified.csv')
parser.add_argument('--fallback-missing-cognate', dest='fallback_cognate', action='store_const', const=True, help='Flag whether to fall back to cognate instead of false friend if neither the English nor the German word was found in the dictionary.')
parser.add_argument('--freedict-en-de', action='store_const', const=True, help='Load the FreeDict English German dictionary.')
parser.add_argument('--freedict-de-en', action='store_const', const=True, help='Load the FreeDict German English dictionary.')
parser.add_argument('--ding', action='store_const', const=True, help='Load the Ding German English dictionary.')
args = parser.parse_args()

if not args.freedict_en_de and not args.freedict_de_en and not args.ding:
	raise Exception("Must at least load specify one dictionary")

dictionary = set()
english_words = set()
german_words = set()

def addAll(dictionary, english_words, german_words, input):
	dictionary2, english_words2, german_words2 = input
	dictionary.update(dictionary2)
	english_words.update(english_words2)
	german_words.update(german_words2)
	
# http://sourceforge.net/projects/freedict/
if args.freedict_en_de:
	print("Reading FreeDict English German dictionary")
	addAll(dictionary, english_words, german_words, readFreeDictDictionary('eng-deu/eng-deu.tei'))

if args.freedict_de_en:
	print("Reading FreeDict German English dictionary")
	addAll(dictionary, english_words, german_words, readFreeDictDictionary('deu-eng/deu-eng.tei', invert=True))

# http://ftp.tu-chemnitz.de/pub/Local/urz/ding/de-en/
if args.ding:
	print("Reading Ding German English dictionary")
	addAll(dictionary, english_words, german_words, readDingDictionary('ding-de-en/de-en.txt', invert=True))

print("Read " + str(len(dictionary)) + " entries")

pairs = 0
gold_pairs = 0.0
gold_correct = 0.0
classified_ff_as_c = 0
classified_c_as_ff = 0

with io.open(args.output, 'w', encoding='utf-8') as o:
	with io.open(args.input, encoding='utf-8') as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			parts = line.split(u"\t")
			assert len(parts) <= 3 and len(parts) >= 2, "bad line: " + line
			
			pairs += 1
			
			english = parts[0]
			if english.startswith(u"to "):
				english = english[3:]
			german = parts[1]
			lookup = english + u"\t" + german
			
			if lookup in dictionary:
				prediction = COGNATE
			else:
				if args.fallback_cognate and english not in english_words and german not in german_words:
					prediction = COGNATE
				else:
					prediction = FALSE_FRIEND
			
			if len(parts) == 3:
				gold_pairs += 1
				solution = int(parts[2])
				if prediction == solution:
					gold_correct += 1
				else:
					if prediction == FALSE_FRIEND:
						classified_c_as_ff += 1
					else:
						classified_ff_as_c += 1
			
			o.write(parts[0])
			o.write(u"\t")
			o.write(parts[1])
			o.write(u"\t")
			o.write(unicode(prediction))
			o.write(u"\n")

		print("Classified " + str(pairs) + " pairs")
		if gold_pairs > 0:
			print("Precision: " + str(gold_correct) + "/" + str(gold_pairs) + " = " + str(gold_correct / gold_pairs))
			print("Classified false friend as cognate: " + str(classified_ff_as_c))
			print("Classified cognate as false friend: " + str(classified_c_as_ff))
