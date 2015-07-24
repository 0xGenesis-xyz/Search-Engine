__author__ = 'Sylvanus'

#from init import similarity
#from init import scores

def recommend(bid):
    booklist = []
    for book in bid:
        for i in similarity[book]:
            booklist.append(i)
    scorelist = []
    for book in booklist:
        scorelist.append((book, scores[book]))
    sorted(scorelist, key=lambda item: item[1])
    return scorelist[:9]
