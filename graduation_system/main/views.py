from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserChangeForm

from django.shortcuts import render, get_object_or_404

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http.response import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from main.models import Process, Task, ProcessForm, TaskForm, ProcessInstance, TaskInstance, UserForm
from django.urls import reverse


@login_required(login_url='/login/')
def index(request):
    return render(request, 'main/index.html')


@login_required(login_url='/login/')
def designer_view(request):
    processes = Process.objects.all()
    return render(request, 'main/designer.html', {'processes': processes})


@login_required(login_url='/login/')
def process_view(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    if request.method == 'POST':
        form = ProcessForm(request.POST, instance=process)
        if form.is_valid():
            form.save()
            messages.success(request, 'Process was successfully edited')
            # return redirect(reverse('process-view'))
            return redirect(request.META.get('HTTP_REFERER'))
    else:
        form = ProcessForm(instance=process)

    return render(request, 'main/process.html', {'process': process, 'form': form})


@login_required(login_url='/login/')
def task_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task was successfully edited')
            return redirect(request.META.get('HTTP_REFERER'))
    else:
        form = TaskForm(instance=task)

    return render(request, 'main/task.html', {'task': task, 'form': form})


@login_required(login_url='/login/')
def task_add(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task has been created')
            return redirect(reverse('process-view', args=[process_id]))
            # return redirect(request.META.get('HTTP_REFERER'))
    else:
        form = TaskForm()
    form.fields["process"].initial = process
    form.fields['process'].widget.attrs['readonly'] = True
    return render(request, 'main/task_add.html', {'form': form})


@login_required(login_url='/login/')
def process_add(request):
    if request.method == 'POST':
        form = ProcessForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Process has been created')
            return redirect(request.META.get('HTTP_REFERER'))
    else:
        form = ProcessForm()
    form.fields['task_start'].widget = forms.HiddenInput()
    form.fields['task_end'].widget = forms.HiddenInput()
    return render(request, 'main/process_add.html', {'form': form})


# new instance of process
@login_required(login_url='/login/')
def process_select(request, process_id):
    user = request.user
    if user.student is None:
        messages.error(request, 'You are not a student')
        return redirect(request.META.get('HTTP_REFERER'))

    process = get_object_or_404(Process, id=process_id)
    instances = process.processinstance_set.filter(student=user.student)
    if len(instances) >= 1:
        messages.error(request, 'Student has selected this process before')
        return redirect(request.META.get('HTTP_REFERER'))

    if process.task_start is None:
        messages.error(request, 'Please specify starting task for this process')
        return redirect(request.META.get('HTTP_REFERER'))

    process_instance = ProcessInstance(student=user.student, process=process, current_task=process.task_start)
    process_instance.save()
    for task in process.task_set.all():
        TaskInstance.objects.create(process_instance=process_instance, task=task)
    messages.success(request, 'Process has been instantiated')
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/login/')
def student_view(request):
    user = request.user
    processes = Process.objects.all()
    if user.student is None:
        messages.error(request, 'You are not a student')
        return redirect(request.META.get('HTTP_REFERER'))
    return render(request, 'main/student_view.html', {'student': user.student , 'processes' : processes})


@login_required(login_url='/login/')
def task_graph(request, process_id):
    process = get_object_or_404(ProcessInstance, id=process_id)
    ordered_task = []
    p = process.process
    t = p.task_start
    i=1
    while 1:
        ordered_task.append(t)
        t = t.next_task_accept
        if t.end_task == True:
            ordered_task.append(t)
            break
        i = i + 1
        if i == 10:
            break
   # return render(request, 'main/task-graph.html', {'process': process.process})
    return render(request, 'main/student_view_timeline.html', {'process': process, 'ordered_task': ordered_task})

# to be changed
@login_required(login_url='/login/')
def student_view_timeline(request):
    process = get_object_or_404(ProcessInstance, id=process_id)
    return render(request, 'main/student_view_timeline.html', {'process': process})


@login_required(login_url='/login/')
def staff_view(request):
    user = request.user
    # group_names = user.groups.values_list('name', flat=True)
    group_names = user.groups.all()
    task_instances = TaskInstance.objects.all().filter(task__group__in=group_names)
    return render(request, 'main/staff-view.html', {'task_instances': task_instances})

@login_required(login_url='/login/')
def process_instance_view(request, p_id):
    process_instance = get_object_or_404(ProcessInstance, id=p_id)
    current_task = process_instance.current_task
    if request.method == 'POST':
        if user.student is not None:
            if request.POST['action'] == 'accept':
                messages.success(request, 'Task successfully accepted')
                process_instance.accept()
            if request.POST['action'] == 'reject':
                messages.success(request, 'Task successfully rejected')
                process_instance.reject()
            if request.POST['action'] == 'staff_done':
                current_task.status = 'student_pending'
        else:
            if request.POST['action'] == 'student_done':
                current_task.status = 'staff_pending'

    process = process_instance.process
    form = ProcessForm(instance=process)
    return render(request, 'main/process-instance.html', {'process_instance': process_instance , 'form' : form})


@login_required(login_url='/login/')
def account_view(request):
    form = UserForm(instance=request.user)
    return render(request, 'main/account.html', {'form': form})
