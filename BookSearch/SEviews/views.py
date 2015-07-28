from django.shortcuts import render
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from SEviews.models import Books #�������ݿ��������
# Create your views here.

from django.http import HttpResponse
from django.shortcuts import render,render_to_response

from search.matrix import Matrix

m = Matrix()

#�ַ�����������������
def SE_Result(wd):
    return list(m.tiered_search(wd))

#��ȡ��Ŀ����
def SE_Recom(bid):
    return list(m.find_most_similar(bid))

#�Լ�鳤�Ƚ��вü�
def summary_cut(book_list):
    summary_len = 110
    for book in book_list:
        if len(book.summary)>=summary_len:
            book.summary=book.summary[:summary_len-3]+"..."
        book.tags = book.tags.split(" ")
    #return book_list

#���Ƽ���Ŀ����������вü�
def title_cut(book_list):
    title_len = 12
    for book in book_list:
        if len(book.title)>=title_len:
            book.title=book.title[:title_len-3]+"..."
    #return book_list

#��Ӧ����������Ҫ����
def result(request):
    #�Ƽ����
    try:
        wd = str(request.GET.get('wd','')) #��ѯ�ֶ�
        page = int(request.GET.get('page','1')) #ҳ�����
    except ValueError:
        page = 1
        wd = ''
    #�հײ�ѯ����ҳ
    if wd=='':
        return render(request,'index.html')
    #�����Ѱ
    else:
        posts_list = SE_Result(wd)                   #�������ݲ������б�
        first_res = posts_list[0]
        recom_list = SE_Recom(first_res)                    #��ȡ�Ƽ����
        page_size=6                                      #ÿҳ��ʾ��Ŀ
        paginator = Paginator(posts_list, page_size)     #ҳ����
        try:
            bids = paginator.page(page)                 #ҳ��ѡ��
        except (EmptyPage, InvalidPage):
            bids = paginator.page(paginator.num_pages)
        posts = []
        recoms= []
        startPos = (page-1)*page_size
        endPos   = startPos + page_size
        #��ȡ�������
        if posts_list:
            for id in posts_list:
                book = Books.objects.filter(bid=id)
                if len(book)>=1:
                    posts.append(book[0])
            none = 0
        #��ȡ�Ƽ���Ŀ
        else:
            none = 1
        for re in recom_list:
            book = Books.objects.filter(bid=re)
            if len(book)>=1:
                recoms.append(book[0])
        title_cut(recoms)
        summary_cut(posts)
        title = wd + " _SynJauNeng"                         #����
        return render_to_response( 'res.html',
        {'name':title,'wd':wd,'none':none,
         'posts':posts,'pages':bids,
         'recoms':recoms,'pid':page})          #�ֵ䴫�ݱ���

def index(request):
    return render(request, 'index.html')
