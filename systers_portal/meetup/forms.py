from django import forms
from django.utils import timezone

from common.forms import ModelFormWithHelper
from common.helpers import SubmitCancelFormHelper
from meetup.models import (Meetup, Rsvp, SupportRequest,
                           RequestMeetup)
from multiupload.fields import MultiFileField
from users.models import SystersUser
from common.models import Comment

from meetup.models import MeetupImages

from meetup.utils import create_meetup

from meetup.utils import edit_meetup, get_meetup


class RequestMeetupForm(ModelFormWithHelper):
    """ Form to create a new Meetup Request. """

    class Meta:
        model = RequestMeetup
        fields = ('title', 'slug', 'date', 'time', 'venue', 'meetup_location', 'description')
        widgets = {'date': forms.DateInput(attrs={'type': 'text', 'class': 'datepicker'}),
                   'time': forms.TimeInput(attrs={'type': 'text', 'class': 'timepicker'})}
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'index' %}"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('created_by')
        super(RequestMeetupForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Override save to add admin to the instance"""
        instance = super(RequestMeetupForm, self).save(commit=False)
        instance.created_by = SystersUser.objects.get(user=self.user)
        if commit:
            instance.save()
        return instance

    def clean_date(self):
        """Check if the date is less than the current date. If so, raise an error."""
        date = self.cleaned_data.get('date')
        if date < timezone.now().date():
            raise forms.ValidationError("Date should not be before today's date.",
                                        code="date_in_past")
        return date

    def clean_time(self):
        """Check that if the date is the current date, the time is not the current time. If so,
        raise an error."""
        time = self.cleaned_data.get('time')
        date = self.cleaned_data.get('date')
        if time:
            if date == timezone.now().date() and time < timezone.now().time():
                raise forms.ValidationError("Time should not be a time that has already passed.",
                                            code="time_in_past")
        return time


class AddMeetupForm(ModelFormWithHelper):
    """Form to create new Meetup. The created_by and the meetup_location of which meetup belong to
    are expected to be provided when initializing the form:

    * created_by - currently logged in user
    * meetup_location - to which Meetup belongs
    """

    class Meta:
        model = Meetup
        fields = ('title', 'slug', 'date', 'time', 'is_virtual', 'meetup_location',
                  'venue', 'description', 'resources')
        widgets = {'date': forms.DateInput(attrs={'type': 'text', 'class': 'datepicker'}),
                   'time': forms.TimeInput(attrs={'type': 'text', 'class': 'timepicker'})}
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'index' %}"

    images = MultiFileField(required=False)

    def __init__(self, *args, **kwargs):
        self.created_by = kwargs.pop('created_by')
        self.leader = kwargs.pop('leader')
        super(AddMeetupForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Override save to add created_by and meetup_location to the instance"""
        instance = super(AddMeetupForm, self).save(commit=False)
        instance.created_by = SystersUser.objects.get(user=self.created_by)
        instance.leader = SystersUser.objects.get(user=self.created_by)
        if instance.is_virtual:
            meet_data = create_meetup(instance)
            instance.meet_link = meet_data['join_url']
            instance.start_url = meet_data['start_url']
            instance.meeting_id = meet_data['id']
        if commit:
            instance.save()
        if self.cleaned_data['images']:
            for img in self.cleaned_data['images']:
                MeetupImages.objects.create(image=img, meetup=instance)
        return instance

    def clean_date(self):
        """Check if the date is less than the current date. If so, raise an error."""
        date = self.cleaned_data.get('date')
        if date < timezone.now().date():
            raise forms.ValidationError("Date should not be before today's date.")
        return date

    def clean_time(self):
        """Check that if the date is the current date, the time is not the current time. If so,
        raise an error."""
        time = self.cleaned_data.get('time')
        date = self.cleaned_data.get('date')
        if time:
            if date == timezone.now().date() and time < timezone.now().time():
                raise forms.ValidationError("Time should not be a time that has already passed.")
        return time


class EditMeetupForm(ModelFormWithHelper):
    """Form to edit Meetup"""

    images = MultiFileField(required=False)

    class Meta:
        model = Meetup
        fields = ('title', 'slug', 'date', 'time', 'description', 'venue',)
        widgets = {'date': forms.DateInput(attrs={'type': 'date', 'class': 'datepicker'}),
                   'time': forms.TimeInput(attrs={'type': 'time', 'class': 'timepicker'})}
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'view_meetup' meetup.slug %}"

    def save(self, commit=True):
        """Override save to add created_by and meetup_location to the instance"""
        instance = super(EditMeetupForm, self).save(commit)
        MeetupImages.objects.filter(meetup=instance).delete()
        if self.cleaned_data['images']:
            for img in self.cleaned_data['images']:
                MeetupImages.objects.create(image=img, meetup=instance)
        if instance.is_virtual:
            edit_meetup(instance)
            meet_data = get_meetup(instance)
            instance.meet_link = meet_data['join_url']
            instance.start_url = meet_data['start_url']
            instance.meeting_id = meet_data['id']
        return instance


class AddMeetupCommentForm(ModelFormWithHelper):
    """Form to add a comment to a Meetup"""

    class Meta:
        model = Comment
        fields = ('body',)
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'view_meetup' meetup.slug %}"

    def __init__(self, *args, **kwargs):
        self.content_object = kwargs.pop('content_object')
        self.author = kwargs.pop('author')
        super(AddMeetupCommentForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Override save to add content_object and author to the instance"""
        instance = super(AddMeetupCommentForm, self).save(commit=False)
        instance.content_object = self.content_object
        instance.author = SystersUser.objects.get(user=self.author)
        if commit:
            instance.save()
        return instance


class EditMeetupCommentForm(ModelFormWithHelper):
    """Form to edit a comment for a Meetup"""

    class Meta:
        model = Comment
        fields = ('body',)
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'view_meetup' meetup.slug %}"


class RsvpForm(ModelFormWithHelper):
    """Form to add RSVP"""

    class Meta:
        model = Rsvp
        fields = ('coming', 'plus_one')
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'view_meetup'  meetup.slug %}"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.meetup = kwargs.pop('meetup')
        super(RsvpForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Override save to add user and meetup to the instance"""
        instance = super(RsvpForm, self).save(commit=False)
        instance.user = SystersUser.objects.get(user=self.user)
        instance.meetup = self.meetup
        if commit:
            instance.save()
        return instance


class AddSupportRequestForm(ModelFormWithHelper):
    """Form to add a new Support Request"""

    class Meta:
        model = SupportRequest
        fields = ('description',)
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'view_meetup' meetup.slug %}"

    def __init__(self, *args, **kwargs):
        self.volunteer = kwargs.pop('volunteer')
        self.meetup = kwargs.pop('meetup')
        super(AddSupportRequestForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Override save to add volunteer and meetup to the instance. Also, send notification to
         all organizers."""
        instance = super(AddSupportRequestForm, self).save(commit=False)
        instance.volunteer = SystersUser.objects.get(user=self.volunteer)
        instance.meetup = self.meetup
        if commit:
            instance.save()
        return instance


class EditSupportRequestForm(ModelFormWithHelper):
    """Form to edit a Support Request"""

    class Meta:
        model = SupportRequest
        fields = ('description',)
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'view_meetup' meetup.slug %}"


class AddSupportRequestCommentForm(ModelFormWithHelper):
    """Form to add a comment to a Support Request"""

    class Meta:
        model = Comment
        fields = ('body',)
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'view_support_request' meetup.slug" \
                             " support_request.pk %}"

    def __init__(self, *args, **kwargs):
        self.content_object = kwargs.pop('content_object')
        self.author = kwargs.pop('author')
        super(AddSupportRequestCommentForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Override save to add content_object and author to the instance"""
        instance = super(AddSupportRequestCommentForm, self).save(commit=False)
        instance.content_object = self.content_object
        instance.author = SystersUser.objects.get(user=self.author)
        if commit:
            instance.save()
        return instance


class EditSupportRequestCommentForm(ModelFormWithHelper):
    """Form to edit a comment for a Support Request"""

    class Meta:
        model = Comment
        fields = ('body',)
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'view_support_request' meetup.slug" \
                             " support_request.pk %}"


class PastMeetup(ModelFormWithHelper):
    images = MultiFileField(required=False)

    class Meta:
        model = Meetup
        fields = ('resources',)
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'view_meetup' meetup.slug %}"

    def save(self, commit=True):
        """Override save to add images to the instance"""
        instance = super(PastMeetup, self).save(commit)
        if self.cleaned_data['images']:
            for img in self.cleaned_data['images']:
                MeetupImages.objects.create(image=img, meetup=instance)
        return instance


class RequestVirtualMeetupForm(ModelFormWithHelper):
    """ Form to create a new Meetup Request. """

    class Meta:
        model = RequestMeetup
        fields = ('title', 'slug', 'date', 'time', 'description')
        widgets = {'date': forms.DateInput(attrs={'type': 'text', 'class': 'datepicker'}),
                   'time': forms.TimeInput(attrs={'type': 'text', 'class': 'timepicker'})}
        helper_class = SubmitCancelFormHelper
        helper_cancel_href = "{% url 'index' %}"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('created_by')
        super(RequestVirtualMeetupForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Override save to add admin to the instance"""
        instance = super(RequestVirtualMeetupForm, self).save(commit=False)
        instance.created_by = SystersUser.objects.get(user=self.user)
        instance.is_virtual = True
        if commit:
            instance.save()
        return instance

    def clean_date(self):
        """Check if the date is less than the current date. If so, raise an error."""
        date = self.cleaned_data.get('date')
        if date < timezone.now().date():
            raise forms.ValidationError("Date should not be before today's date.",
                                        code="date_in_past")
        return date

    def clean_time(self):
        """Check that if the date is the current date, the time is not the current time. If so,
        raise an error."""
        time = self.cleaned_data.get('time')
        date = self.cleaned_data.get('date')
        if time:
            if date == timezone.now().date() and time < timezone.now().time():
                raise forms.ValidationError("Time should not be a time that has already passed.",
                                            code="time_in_past")
        return time
