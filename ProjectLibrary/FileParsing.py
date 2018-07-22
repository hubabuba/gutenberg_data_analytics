import glob
import string
import os
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import numpy as np


class TextProcessor:
    def __init__(self,basePath,useRandomSet=False,nRandomTitles=100):
        '''
        create an instance of text processor. This will load data from the hard drive, support parse the text from the files
        conduct preprocessing steps and convert it into BOW representation.
        :param useRandomSet: set to true if a random selection of books shall be used, otherwise the HSD dataset is used
        :param basaPath: the datapath for the gutenberg date
        '''
        self._stop_words = set(stopwords.words('english'))
        self._ps = PorterStemmer()
        self._preprocessedTexts = {}
        self._minLength = 3
        if useRandomSet:
            self._basePath=os.path.join(basePath,"gutenberg_data")
        else:
            self._basePath =os.path.join(basePath,"gutenberg_books_sorted")
        self._useRandomSet=useRandomSet
        self._preamble_len = len("The Project Gutenberg EBook")
        self._nLinesToIgnore = 100
        self._minDocumentLength = 100000
        self._nRandomTitles=nRandomTitles

        self._endOfBookMarkers = ['*** end', 'End of this Project Gutenberg', '***end', 'End of The Project Gutenberg',
                            'End of Project Gutenberg', 'End of PG']



    def initializeRandomSet(self):
        '''
        Randomly choose the configured number of titles from the repository. Books will be opened and only added to the repository if they meet the quality criteria.
        Quality criteria include minimal document length, that an end of the real text can be found (to avoid cluttering the data with licence text and similar).
        See constructor of class for configuration details
        :return: None
        '''
        #
        np.random.seed(4)
        if self._useRandomSet:
            doc_list = glob.glob(os.path.join(self._basePath, "*.txt"))
            self._gutenberg_selection = []
            nSuccess = 0
            while nSuccess < self._nRandomTitles:
                book_path = np.random.choice(doc_list, 1,replace=False)[0]
                if not book_path in self._gutenberg_selection:
                    author, title, full_text, endFound = self.openFileWithIds(book_path)

                    if self.checkIfUse(author, title, full_text, endFound):
                        self._gutenberg_selection.append(book_path)
                        nSuccess += 1
        self._gutenberg_selection.sort()

    def reset(self):
        self._preprocessedTexts={}
        self._gutenberg_selection=[]

    def preProcessText(self,text ,title,useStemmer=True):
        '''
        This function takes a full text (extracted by the function openFileWithIds) and returns a list of words whitespace, punctuation as well as
        stopwords, invalid words and not adequately encoded words removed.
        It also provides an option to use a stemmer
        :param text: String, full text of the book as a string.
        :param title: will be used as a key in a dictionary to store the already preprocessed text for performance gains
        :param useStemmer: Set to True if stemmer shall be used, false otherwise. Porter stemmer is used
        :return: representation of the text as a list of words
        '''

        if title in self._preprocessedTexts:
            return self._preprocessedTexts[title]

        text =text.lower()
        text =text.translate(string.maketrans('' ,'') ,string.punctuation)
        text_list =word_tokenize(text)
        text_list =[w for w in text_list if not w in self._stop_words]
        text_list = [w for w in text_list if (w.isalpha() and len(w) >self._minLength)]
        final_list =[]
        for w in text_list:
            try:
                w=w.decode('utf-8')
                if useStemmer:
                    final_list.append(self._ps.stem(w))
                else:
                    final_list.append(w)
            # some words seem to be not in the encoding mentioned in the respective files. Ignore those
            except UnicodeError:
                print "unicode error"
                continue
            except Exception as e:
                print "unknown exception"
                print e
        self._preprocessedTexts[title]=final_list
        return final_list


    def openFileWithIds(self,filepath):

        '''
        opens a file at filepath, parses it and returns book author, title, full text (with no meta information) as well as whether and end could be parsed in the book
        :param filepath:
        :return: quadruplet author(string), title(string),full_text(string), endFound (boolean)
        '''

        try:
            f=open(filepath)
            lines=f.readlines()
        except Exception as e:
            print "something went wrong with the file, ignoring it"
            print e
            return "unknown","unknown","",False


        complete_text="".join(lines)

        ########## title search #################
        titid=complete_text.find('Title: ')
        if titid>0:
            title=complete_text[titid+7:complete_text.find('\n',titid)].strip()
        else:
            title_line=lines[0][self._preamble_len:]
            ofp=title_line.find('of')
            if ofp >=0:
                title=title_line[ofp+3:title_line.find('\n')].strip()
            else:
                title="unknown"

        ########## author search #######################
        autid=complete_text.find('Author: ')
        if autid>0:
            author=complete_text[autid+8:complete_text.find('\n',autid)].strip()
        else:
            author_line=lines[1]
            aut_indx=author_line.find('by')
            if aut_indx >=0:
                author=author_line[aut_indx+3:author_line.find('\n')].strip()
            else:
                author="unknown"

        ##########decode text#####################
        encid=complete_text.find('encoding')

        if encid>=0:
            encoding=complete_text[encid+10:encid+30].strip()
            encoding=encoding[0:encoding.find('\n')]
        else:
            #attempt standard encoding
            encoding='UTF-8'

        full_text="".join(lines[self._nLinesToIgnore:])

        tempEndOfBookMarkers=self._endOfBookMarkers+["end of "+title.lower()]
        endFound=False
        full_text_low=full_text.lower()
        for eobm in tempEndOfBookMarkers:

            eob=full_text_low.find(eobm.lower())
            if eob>0:
                endFound=True
                break
        if not endFound:
            print "end not found for filepath"+filepath
            print filepath

        if encoding=='ISO-8859-1':
            full_text=full_text.decode('ISO-8859-1').encode('utf-8')
        elif encoding in ['Latin-1','ISO Latin-1','Latin1','ISO-Latin-1']:
            full_text=full_text.decode('Latin-1').encode('utf-8')
        elif encoding in ['UTF-8','ASCII','ASCII (with a few I','ASCII, with a few I']:
            full_text=full_text.decode('utf-8','ignore').encode("utf-8")
            #many of the text have errouns ascii or utf-8 encoding.
            #remove all erronous symbols and print
        else:
            #print "cannot recognize encoding, running with standard and ignoring errors"
            full_text=full_text.decode('utf-8','ignore').encode("utf-8")

        f.close()

        return author,title,full_text,endFound



    def checkIfUse(self,author,title,full_text,endFound):
        '''
        check if the document is a valid document
        :param author:
        :param title:
        :param full_text:
        :param endFound:
        :return:
        '''

        if len(author)>0 and len(title)>0 and len(full_text)>self._minDocumentLength and endFound:
            return True
        else:
            return False

    def pathIterator(self):
        '''
        Iterator which returns paths to books
        :return: iterator, returns one path to a text file for each call
        '''
        if self._useRandomSet:
            for b in self._gutenberg_selection:
                yield os.path.normpath(b)
        else:
            dir_list =glob.glob(os.path.join(self._basePath,"*"))
            book_list=[]
            for d in dir_list:
                bookDirPath =os.path.join(self._basePath ,d ,"*.txt")
                book_list += glob.glob(bookDirPath)
            for b in book_list:
                yield os.path.normpath(b)


    def returnAllPaths(self):
        '''
        Return a list containing all paths. Calls on the path iterator defined above and fills the paths into a list
        :return: list of all paths in the
        '''
        allPaths=[]
        for p in self.pathIterator():
            author,title,full_text,endFound=self.openFileWithIds(p)
            if self.checkIfUse(author,title,full_text,endFound):
                allPaths.append(p)
        return allPaths

    def extractCategory(self,filepath):
        '''
        Used for the HSD dataset. Human defined categories are represented by folder, this function parses the folder
        :param filepath: textpath to the textfile
        :return: string, category
        '''
        if not os.path.exists(filepath):
            raise ValueError("Invalid Path, please check")

        category =filepath.split('\\')[-2]
        return category


#Corpus class for LDA Model. To avoid loading all data at the same time, creates an iterator which can be called by gensim
class Corpus(object):
    def __init__(self, dictionary,textProcessor):
        self._full_docs = []
        self._textProcessor=textProcessor
        paths = self._textProcessor.returnAllPaths()
        for p in paths:
            author, title, full_text, endFound = self._textProcessor.openFileWithIds(p)
            doc = dictionary.doc2bow(self._textProcessor.preProcessText(full_text, title))
            self._full_docs.append(doc)

    def __iter__(self):
        for doc in self._full_docs:
            yield doc