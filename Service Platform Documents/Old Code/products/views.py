from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product

@login_required
def product_list_view(request):
    """
    Display list of products matching the style of the dashboard.
    """
    # Sorting logic
    sort_by = request.GET.get('sort', 'name')
    direction = request.GET.get('direction', 'asc')
    
    # Map friendly URL names to model fields if necessary, or validate
    valid_sorts = {
        'name': 'name',
        'sku': 'sku', 
        'category': 'category',
        'type': 'product_type',
        'price': 'price',
        'stock': 'quantity_on_hand',
        'status': 'status'
    }
    
    sort_field = valid_sorts.get(sort_by, 'name')
    
    # Toggle direction for next click (handled in template usually, but we need current for query)
    order_prefix = '-' if direction == 'desc' else ''
    
    products = Product.objects.all().order_by(f"{order_prefix}{sort_field}")
    
    context = {
        'products': products,
        'page_title': 'Product List',
        'current_sort': sort_by,
        'current_direction': direction
    }
    return render(request, "products/product_list.html", context)

from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Product

class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Navigation Logic (Next/Previous)
        # Default ordering is 'name' from Meta
        current_product = self.get_object()
        
        # This is a simple implementation. For large datasets, use cursor/index optimization.
        # Assuming ordering by 'name'.
        
        # Next: name > current.name
        next_p = Product.objects.filter(name__gt=current_product.name).order_by('name').first()
        # Prev: name < current.name (order by desc)
        prev_p = Product.objects.filter(name__lt=current_product.name).order_by('-name').first()
        
        if next_p:
            context['next_object_url'] = reverse_lazy('product_detail', kwargs={'pk': next_p.pk})
        if prev_p:
            context['previous_object_url'] = reverse_lazy('product_detail', kwargs={'pk': prev_p.pk})
            
        return context

class ProductCreateView(CreateView):
    model = Product
    template_name = "products/product_form.html"
    fields = ['sku', 'name', 'status', 'date_started', 'category', 'product_type', 'quantity_on_hand', 'price', 'description', 'image']
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class ProductUpdateView(UpdateView):
    model = Product
    template_name = "products/product_form.html"
    fields = ['sku', 'name', 'status', 'date_started', 'category', 'product_type', 'quantity_on_hand', 'price', 'description', 'image']
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('product_detail', kwargs={'pk': self.object.pk})

class ProductDeleteView(DeleteView):
    model = Product
    template_name = "products/product_confirm_delete.html"
    success_url = reverse_lazy('product_list')
