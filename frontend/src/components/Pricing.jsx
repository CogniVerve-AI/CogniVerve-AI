import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Check, X, CreditCard, Loader2 } from 'lucide-react'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { api } from '../services/api'

const PricingPage = () => {
  const [plans, setPlans] = useState({})
  const [currentPlan, setCurrentPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [subscribing, setSubscribing] = useState(null)

  useEffect(() => {
    fetchPlans()
    fetchCurrentSubscription()
  }, [])

  const fetchPlans = async () => {
    try {
      const response = await api.get('/billing/plans')
      setPlans(response.data.data.plans)
    } catch (error) {
      console.error('Failed to fetch plans:', error)
    }
  }

  const fetchCurrentSubscription = async () => {
    try {
      const response = await api.get('/billing/current')
      setCurrentPlan(response.data.plan)
    } catch (error) {
      console.error('Failed to fetch current subscription:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubscribe = async (planName) => {
    if (planName === 'free') return
    
    setSubscribing(planName)
    try {
      const response = await api.post('/billing/create-checkout-session', {
        plan: planName,
        billing_cycle: 'monthly'
      })
      
      // Redirect to Stripe checkout
      window.location.href = response.data.data.checkout_url
    } catch (error) {
      console.error('Failed to create checkout session:', error)
      alert('Failed to start subscription process. Please try again.')
    } finally {
      setSubscribing(null)
    }
  }

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription?')) return
    
    try {
      await api.post('/billing/cancel')
      alert('Subscription cancelled successfully')
      fetchCurrentSubscription()
    } catch (error) {
      console.error('Failed to cancel subscription:', error)
      alert('Failed to cancel subscription. Please try again.')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Scale your AI agent capabilities with flexible pricing plans designed for every need
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {Object.entries(plans).map(([planKey, plan]) => (
            <motion.div
              key={planKey}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Object.keys(plans).indexOf(planKey) * 0.1 }}
            >
              <Card className={`relative h-full ${
                planKey === 'pro' ? 'border-blue-500 shadow-lg scale-105' : ''
              } ${currentPlan === planKey ? 'ring-2 ring-green-500' : ''}`}>
                {planKey === 'pro' && (
                  <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-blue-500">
                    Most Popular
                  </Badge>
                )}
                
                {currentPlan === planKey && (
                  <Badge className="absolute -top-3 right-4 bg-green-500">
                    Current Plan
                  </Badge>
                )}

                <CardHeader className="text-center">
                  <CardTitle className="text-2xl font-bold">{plan.name}</CardTitle>
                  <CardDescription>
                    <div className="mt-4">
                      <span className="text-4xl font-bold text-gray-900">
                        ${plan.price}
                      </span>
                      <span className="text-gray-600">/month</span>
                    </div>
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>API Calls</span>
                      <span className="font-medium">
                        {plan.api_calls_limit === -1 ? 'Unlimited' : plan.api_calls_limit.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Compute Time</span>
                      <span className="font-medium">
                        {plan.compute_minutes_limit === -1 ? 'Unlimited' : `${plan.compute_minutes_limit} min`}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Storage</span>
                      <span className="font-medium">
                        {plan.storage_gb_limit === -1 ? 'Unlimited' : `${plan.storage_gb_limit}GB`}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Agents</span>
                      <span className="font-medium">
                        {plan.agents_limit === -1 ? 'Unlimited' : plan.agents_limit}
                      </span>
                    </div>
                  </div>

                  <div className="pt-4 border-t">
                    <ul className="space-y-2">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-center text-sm">
                          <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>

                <CardFooter>
                  {currentPlan === planKey ? (
                    <div className="w-full space-y-2">
                      <Button variant="outline" className="w-full" disabled>
                        Current Plan
                      </Button>
                      {planKey !== 'free' && (
                        <Button 
                          variant="destructive" 
                          size="sm" 
                          className="w-full"
                          onClick={handleCancelSubscription}
                        >
                          Cancel Subscription
                        </Button>
                      )}
                    </div>
                  ) : (
                    <Button
                      className={`w-full ${
                        planKey === 'pro' ? 'bg-blue-600 hover:bg-blue-700' : ''
                      }`}
                      onClick={() => handleSubscribe(planKey)}
                      disabled={subscribing === planKey}
                    >
                      {subscribing === planKey ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          {planKey === 'free' ? 'Get Started' : (
                            <>
                              <CreditCard className="h-4 w-4 mr-2" />
                              Subscribe
                            </>
                          )}
                        </>
                      )}
                    </Button>
                  )}
                </CardFooter>
              </Card>
            </motion.div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">
            Frequently Asked Questions
          </h2>
          
          <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="text-left">
              <h3 className="font-semibold text-lg mb-2">Can I change plans anytime?</h3>
              <p className="text-gray-600">
                Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately.
              </p>
            </div>
            
            <div className="text-left">
              <h3 className="font-semibold text-lg mb-2">What happens if I exceed my limits?</h3>
              <p className="text-gray-600">
                Your requests will be temporarily limited until you upgrade your plan or the next billing cycle begins.
              </p>
            </div>
            
            <div className="text-left">
              <h3 className="font-semibold text-lg mb-2">Is there a free trial?</h3>
              <p className="text-gray-600">
                Yes, all new users start with our free plan. No credit card required to get started.
              </p>
            </div>
            
            <div className="text-left">
              <h3 className="font-semibold text-lg mb-2">Can I cancel anytime?</h3>
              <p className="text-gray-600">
                Absolutely. You can cancel your subscription at any time with no cancellation fees.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PricingPage

