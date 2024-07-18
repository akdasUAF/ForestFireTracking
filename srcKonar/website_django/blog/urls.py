from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('',views.home,name='blog-home'),
    path('about/',views.about,name='blog-about'),
    path('contact/',views.contact,name='blog-contact'),
    path('model_specification/', views.model_specification, name='model_specification'),
    path('try_demo/', views.try_demo, name='try_demo'),  
    path('results/', views.results, name='results'),
    path('model_compare/', views.model_compare, name='model_compare'),   
    path('model_compare_results/', views.model_compare_results, name='model_compare_results'),
   
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
