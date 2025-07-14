from django.http import JsonResponse
from django.views.generic import CreateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json

@method_decorator(csrf_exempt, name='dispatch')
class FundLoadView(View):
    """
    Process a fund load request.

    This is a placeholder implementation that will be replaced with your actual logic.
    The tests will guide the implementation of the velocity limits and other requirements.
    """

    def post(self, request, *args, **kwargs):
        try:
            # Parse the request body
            data = json.loads(request.body)

            # Extract the relevant fields
            load_id = data.get('id')
            customer_id = data.get('customer_id')
            load_amount = data.get('load_amount')
            time = data.get('time')

            # This is where your implementation will go to check the velocity limits
            # For now, we'll just return a placeholder response

            # Return a response
            return JsonResponse({
                'id': load_id,
                'customer_id': customer_id,
                'accepted': True  # This will be determined by your implementation
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def get(self, request, *args, **kwargs):
        return JsonResponse({'error': 'Method not allowed'}, status=405)
