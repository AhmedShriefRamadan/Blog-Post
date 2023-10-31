from django.shortcuts import render,get_object_or_404,redirect
from django.core.paginator import Paginator,EmptyPage,\
                                PageNotAnInteger
# from django.views.generic import ListView
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import TrigramSimilarity
from django.contrib.auth import logout, login, authenticate
from django.views import View
from django.contrib.auth.models import User, Group
from PIL import Image
from django.utils.text import slugify
from django.contrib import messages
from django.http import JsonResponse,HttpResponseForbidden,HttpResponse
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password





# from django.http import Http404

from .models import Post,Comment,UserProfile,Category,CompanyProfile
from .forms import EmailPostForm,CommentForm,SearchForm,UserRegisterForm,UserLoginForm,AddCategory,CompanyRegistration,EditUserProfile,ChangeForm


def post_list(request, tag_slug=None):

    response = post_search(request)
    search_form = response['form']
    post_list = Post.published.all()

    tag=None
    if tag_slug:
        tag = get_object_or_404(Tag,slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    
    paginator = Paginator(post_list,4)
    page_number = request.GET.get('page',1)
    
    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        posts = paginator.page(1)

    return render(request,'blog/post/list.html',
                {'posts':posts,
                'tag':tag,
                'form':search_form})




def post_detail(request,year,month,day,post):

    post = get_object_or_404(Post,
                            status=Post.Status.PUBLISHED,
                            slug=post,
                            publish__year=year,
                            publish__month=month,
                            publish__day=day)
    comments = post.comments.filter(active=True)
    form = CommentForm()

    category = post.category
    post_tags_ids = post.tags.values_list('id',flat=True)

    similar_posts = Post.published.filter(tags__in=post_tags_ids)\
                                    .exclude(id=post.id)
    
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
                                    .order_by('-same_tags','-publish','category')
    paginator = Paginator(similar_posts,2)
    page_number = request.GET.get('page',1)

    try:
        similar_posts = Paginator.page(paginator,page_number)
    except EmptyPage:
        similar_posts = Paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        similar_posts = Paginator.page(1)

    
    
    return render(request,'blog/post/detail.html',
                {'post':post,
                'comments':comments,
                'form':form,
                'similar_posts':similar_posts})



def post_share(request,post_id):
    post = get_object_or_404(Post,id=post_id,status=Post.Status.PUBLISHED)
    sent = False

    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read "\
                        f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                        f"{cd['name']}\'s comments: {cd['comments']}"
            
            send_mail(subject, message ,'ahmedshrieframadan@gmail.com',[cd['to']])
            sent = True

    else:
        form = EmailPostForm()
    return render(request,'blog/post/share.html',{'post':post,
                                                'form':form,
                                                'sent':sent})


@require_POST
def post_comment(request,post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(request,'blog/post/comment.html',
                {'post':post,
                'form':form,
                'comment':comment})



def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']

            results = Post.published.annotate(
                            similarity=TrigramSimilarity('title', query)
                            + TrigramSimilarity('body', query)) \
                            .filter(similarity__gt=0.04).order_by("-similarity")

    context = {'form':form,
                'query':query,
                'results':results}

    return context


def home(request):
    numbers_list = range(1, 1000)
    page = request.GET.get('page', 1)
    paginator = Paginator(numbers_list, 100)
    try:
        numbers = paginator.page(page)
    except PageNotAnInteger:
        numbers = paginator.page(1)
    except EmptyPage:
        numbers = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/test.html', {'numbers': numbers})


class loginView (View):
    def get(self, request):
        form = UserLoginForm()
        return render(request, 'blog/users/login.html', {'form': form})

    def post(self, request):
        print(request.user)
        form = UserLoginForm(request.POST)

        if form.is_valid():
            username = f"{form.cleaned_data['username']}"
            password = f"{form.cleaned_data['password']}"
            print(username)
            print(password)
            user = authenticate(request, username=username, password=password)
            print(user)
            if user:
                login(request, user)
                return redirect('blog:profile',user)
            else:
                messages.error(
                    request, 'Invalid username or password.')
                return redirect('blog:login')
        else:
            messages.error(
                request, "Wrong input data please re enter it.")
            return redirect('blog:login')



class RegisterView(View):
    def get(self, request):
        form = None
        if (request.GET.get('status') == 'company'):
            form = CompanyRegistration()
        else:
            form = UserRegisterForm()
        return render(request, 'blog/users/register.html', {'form': form, 'status': request.GET.get('status')})

    def post(self, request):
        filterData = request.POST.copy()
        is_company = filterData['data'] == 'company'
        del filterData['data']
        if (is_company):
            form = CompanyRegistration(request.POST)
        else:
            form = UserRegisterForm(request.POST)
        if form.is_valid():
            if (is_company):
                contact1 = form.cleaned_data['contact1'] or None
                contact2 = form.cleaned_data['contact2'] or None
                user_admin = get_object_or_404(User, username = form.cleaned_data['admin'])
                CompanyProfile.objects.create(
                    company_name=form.cleaned_data['company_name'], description=form.cleaned_data['description'],contact1=contact1,contact2=contact2,admin=user_admin)
                form.save()
                group = get_object_or_404(Group, name='Company')
                user_admin.groups.add(group)
                user.save()
                redirect('blog:login')
            else:
                form.save()
                user = get_object_or_404(
                    User, username=form.cleaned_data['username'])
                UserProfile.objects.create(user=user)
                user.first_name = form.cleaned_data['first']
                user.last_name = form.cleaned_data['last']

                if form.cleaned_data['is_superuser'] == True:
                    group = get_object_or_404(Group, name="Admin-Group")
                    user.is_staff = True
                else:
                    group = get_object_or_404(Group, name='User-Group')

                user.groups.add(group)
                user.save()
                user = authenticate(
                    request, username=f"{form['username'].value()}", password=f"{form['password1'].value()}")
                login(request, user)
                return redirect('blog:post_list')
        else:
            messages.error(
                request, "Wrong input data please re enter it.")
            return JsonResponse({"message": "wrong"})


class ProfileView(View):
    def get(self,request,user):
        current_user = get_object_or_404(User, username=user)
        user = get_object_or_404(UserProfile,user=request.user)
        if current_user.id != user.id:
            return HttpResponseForbidden()
        writer_in_companies = current_user.user_writer.all() or None
        admin_in_companies = current_user.company_admin.all() or None

        if request.GET.get('status') == 'draft':
            posts = Post.objects.filter(author=current_user.id,status='DF')
        
        else:
            posts = Post.published.filter(author=current_user.id)

        profile = get_object_or_404(UserProfile, user=current_user.id)

        return render(request,'blog/users/profile.html',
                    {'user':current_user,
                    'writer_in_companies':writer_in_companies,
                    'admin_in_companies':admin_in_companies,
                    'posts':posts,
                    'profile':profile})
    


class PorfileViewPK(View):
    def get(self,request,pk):
        form = EditUserProfile
        return render(request,'blog/users/edite_profile.html',{'form':form})

    def post(self,request,pk):
        user = get_object_or_404(User, id=pk)
        if request.user == user:
            firstname = request.POST['firstname'] or None
            lastname = request.POST['lastname'] or None
            email = request.POST['email'] or None
            form = EditUserProfile(request.POST,request.FILES)
            if form.is_valid():
                image = form.cleaned_data['image'] or None
                badge = form.cleaned_data['badge'] or None
                link1 = form.cleaned_data['link1'] or None
                link2 = form.cleaned_data['link2'] or None
                if firstname:
                    user.first_name = firstname
                if lastname:
                    user.last_name = lastname
                if email:
                    user.email = email
                profile = get_object_or_404(UserProfile, user=user.id)
                if image:
                    profile.image = image
                if badge:
                    profile.badge = badge
                if link1:
                    profile.link1 = link1
                if link2:
                    profile.link2 = link2
                user.save()
                profile.save()
                return redirect('blog:profile', user)
    

def delete_account(request,user):
    if request.method == 'GET':
        logout(request)
        get_object_or_404(User, username=user).delete()
        return redirect('blog:post_list')
    else:
        return HttpResponse('Bad request')


class changePass (PasswordChangeView):
    def get(self, request):
        form = ChangeForm
        return render(request, 'blog/users/change_password.html', {'form': form})

    def post(self, request):
        form = ChangeForm(request.POST)
        if (form.is_valid()):
            if check_password(form['old_password'].value(), request.user.password) and (form['new_password1'].value() == form['new_password2'].value()):

                request.user.set_password(form['new_password1'].value())
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(
                    request, "Your password changed")
                return redirect('blog:profile', request.user)
            else:
                messages.error(
                    request, "Wrong input data")
                return redirect('blog:change_pass')
        else:
            messages.error(
                request, "Wrong input data")
        return redirect('blog:change_pass')





def category_detail(request, name):
    category_name = get_object_or_404(Category,name=name)
    posts = category_name.post_category.all()
    return render(request, 'blog/post/category_detail.html', {'posts':posts,'name':category_name})

def categories_list(request):
    check = False
    form = None
    if request.GET.get('category') == 'add':
        form = AddCategory()
        check = True

    if request.method == 'POST':
        form = AddCategory(request.POST,request.FILES)
        if form.is_valid():
            upload_file = form.cleaned_data['image']
            image_name = upload_file.name
            name = form.cleaned_data['name']
            form.save()
            
            image_path = f'media/images/categories/{name}/{image_name}'
            image = Image.open(image_path)
            new_image = image.resize((500,80))
            new_image.save(image_path)
            form.cleaned_data['image'] = new_image
            form.save()
            
            check=False


    categories = Category.objects.all()
    return render(request, 'blog/post/categories.html',
                {'categories':categories,
                'form':form,
                'check':check})


def add_post(request):
    
    if request.method == 'POST':
        category = get_object_or_404(Category,name=request.POST['categories'])
        tags = request.POST.getlist('tags')
        post = Post.objects.create(title=request.POST['title'],
                            slug=slugify(request.POST['title']),
                            body=request.POST['content'],
                            status=request.POST['status'] or None,
                            author=request.user,
                            category=category or None)
        if tags:
            post.tags.set(tags)
        post.save()

    categories = Category.objects.all()
    tags = Tag.objects.all()

    return render(request,'blog/post/create.html',{'categories':categories,
                                                'tags':tags})


def add_tag(request):
    tag = request.GET.get('tag')
    if tag :
        Tag.objects.create(name=tag)

    return redirect('blog:post_list')