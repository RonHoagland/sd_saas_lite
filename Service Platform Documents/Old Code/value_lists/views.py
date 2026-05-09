from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import ValueList, ValueItem
from django import forms

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class ValueListDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = ValueList
    template_name = "value_lists/value_list_confirm_delete.html"
    success_url = reverse_lazy('value_list_list')

    def dispatch(self, request, *args, **kwargs):
        # Additional safety check before GET or POST
        self.object = self.get_object()
        if self.object.items.exists():
            messages.error(request, "Cannot delete this list because it contains items. Please delete all options first.")
            return redirect('value_list_detail', slug=self.object.slug)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, f"Value List '{self.get_object().name}' deleted.")
        return super().delete(request, *args, **kwargs)

class ValueItemDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = ValueItem
    template_name = "value_lists/value_item_confirm_delete.html"
    
    def get_success_url(self):
        return reverse('value_list_detail', kwargs={'slug': self.object.value_list.slug})

    def delete(self, request, *args, **kwargs):
        messages.success(request, f"Option '{self.get_object().value}' deleted.")
        return super().delete(request, *args, **kwargs)

class ValueListListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = ValueList
    template_name = "value_lists/value_list_list.html"
    context_object_name = "value_lists"

class ValueListCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = ValueList
    fields = ['name', 'description']
    template_name = "value_lists/value_list_form.html"
    success_url = reverse_lazy('value_list_list')

    def form_valid(self, form):
        from django.utils.text import slugify
        form.instance.slug = slugify(form.instance.name)
        messages.success(self.request, f"Value List '{form.instance.name}' created.")
        return super().form_valid(form)

class ValueListDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = ValueList
    template_name = "value_lists/value_list_detail.html"
    context_object_name = "value_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get items for this list
        context['items'] = self.object.items.all()
        return context

class ValueListUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = ValueList
    fields = ['name', 'description'] # Slug should ideally not be changed after creation to avoid breaking code references
    template_name = "value_lists/value_list_form.html"
    
    def get_success_url(self):
        return reverse('value_list_detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        messages.success(self.request, f"Value List '{form.instance.name}' updated.")
        return super().form_valid(form)

class ValueItemCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = ValueItem
    fields = ['value', 'sort_order', 'is_active']
    template_name = "value_lists/value_item_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['value_list'] = get_object_or_404(ValueList, slug=self.kwargs['slug'])
        return context

    def form_valid(self, form):
        value_list = get_object_or_404(ValueList, slug=self.kwargs['slug'])
        form.instance.value_list = value_list
        messages.success(self.request, f"Item '{form.instance.value}' added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('value_list_detail', kwargs={'slug': self.kwargs['slug']})

class ValueItemUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = ValueItem
    fields = ['value', 'sort_order', 'is_active']
    template_name = "value_lists/value_item_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['value_list'] = self.object.value_list
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Item '{form.instance.value}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('value_list_detail', kwargs={'slug': self.object.value_list.slug})
