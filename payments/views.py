from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.conf import settings
import stripe
from core.models import User
from .models import PaymentRecord, PaymentRefund
from .serializers import PaymentRecordSerializer, PaymentRefundSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == User.Role.STUDENT:
            return PaymentRecord.objects.filter(user=self.request.user)
        elif self.request.user.role == User.Role.TEACHER:
            return PaymentRecord.objects.filter(metadata__teacher_id=self.request.user.id)
        return PaymentRecord.objects.none()
        return Payment.objects.none()

    @action(detail=True, methods=['post'])
    def create_payment_intent(self, request, pk=None):
        payment = self.get_object()
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # Convert to cents
                currency=payment.currency,
                metadata={
                    'payment_id': payment.id,
                    'booking_id': payment.booking.id
                }
            )
            
            payment.stripe_payment_intent_id = intent.id
            payment.save()
            
            return Response({
                'clientSecret': intent.client_secret
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        payment = self.get_object()
        
        try:
            intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
            
            if intent.status == 'succeeded':
                payment.status = 'completed'
                payment.save()
                return Response({'status': 'payment confirmed'})
            else:
                return Response({
                    'error': 'Payment has not been completed'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PaymentRefundViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentRefundSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_profile = self.request.user.profile
        if user_profile.role == 'student':
            return PaymentRefund.objects.filter(payment__student=user_profile)
        elif user_profile.role == 'teacher':
            return PaymentRefund.objects.filter(payment__booking__teacher__user_profile=user_profile)
        return PaymentRefund.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment = serializer.validated_data['payment']
        amount = serializer.validated_data['amount']
        
        try:
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=int(amount * 100)  # Convert to cents
            )
            
            serializer.validated_data['stripe_refund_id'] = refund.id
            self.perform_create(serializer)
            
            payment.status = 'refunded'
            payment.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
