from rest_framework import serializers

from .models import SequenceAnnotation
from .models import Label, Project, Document


class LabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields = ('id', 'text', 'shortcut', 'background_color', 'text_color')


class DocumentSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(DocumentSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = Document
        fields = ('id', 'text', 'annotated')

    def update(self, instance, validated_data):
        instance.annotated = validated_data.get('annotated', instance.annotated)
        instance.save()
        return instance

    def create(self, validated_data):
        docs = [Document(**item) for item in validated_data]
        return Document.objects.bulk_create(docs)

class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'guideline', 'users', 'image', 'updated_at')


class ProjectFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):

    def get_queryset(self):
        view = self.context.get('view', None)
        request = self.context.get('request', None)
        queryset = super(ProjectFilteredPrimaryKeyRelatedField, self).get_queryset()
        if not request or not queryset or not view:
            return None
        return queryset.filter(project=view.kwargs['project_id'])


class SequenceAnnotationSerializer(serializers.ModelSerializer):
    label = ProjectFilteredPrimaryKeyRelatedField(queryset=Label.objects.all())

    class Meta:
        model = SequenceAnnotation
        fields = ('id', 'prob', 'label', 'start_offset', 'end_offset')

    def create(self, validated_data):
        annotation = SequenceAnnotation.objects.create(**validated_data)
        return annotation


class SequenceDocumentSerializer(serializers.ModelSerializer):
    annotations = serializers.SerializerMethodField()

    def get_annotations(self, instance):
        request = self.context.get('request')
        if request:
            annotations = instance.seq_annotations.filter(user=request.user)
            serializer = SequenceAnnotationSerializer(annotations, many=True)
            return serializer.data

    class Meta:
        model = Document
        fields = ('id', 'text', 'annotations', 'annotated')

