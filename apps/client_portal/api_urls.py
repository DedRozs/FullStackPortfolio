from rest_framework.routers import DefaultRouter

from apps.client_portal.infrastructure.viewsets import (
    ActivityEventViewSet,
    ApprovalViewSet,
    ClientOrganizationViewSet,
    DeliverableVersionViewSet,
    DeliverableViewSet,
    FileRecordViewSet,
    InvoiceRecordViewSet,
    MessageThreadViewSet,
    MessageViewSet,
    MilestoneViewSet,
    ProjectViewSet,
    UserProfileViewSet,
)

router = DefaultRouter()
router.register('organizations', ClientOrganizationViewSet, basename='clientorganization')
router.register('profiles', UserProfileViewSet, basename='userprofile')
router.register('projects', ProjectViewSet, basename='project')
router.register('milestones', MilestoneViewSet, basename='milestone')
router.register('deliverables', DeliverableViewSet, basename='deliverable')
router.register('deliverable-versions', DeliverableVersionViewSet, basename='deliverableversion')
router.register('approvals', ApprovalViewSet, basename='approval')
router.register('threads', MessageThreadViewSet, basename='messagethread')
router.register('messages', MessageViewSet, basename='message')
router.register('files', FileRecordViewSet, basename='filerecord')
router.register('invoices', InvoiceRecordViewSet, basename='invoicerecord')
router.register('activity', ActivityEventViewSet, basename='activityevent')

urlpatterns = router.urls
