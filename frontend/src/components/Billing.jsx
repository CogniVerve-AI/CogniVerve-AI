import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  CreditCard, 
  TrendingUp, 
  Calendar, 
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Progress } from '../components/ui/progress'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { api } from '../services/api'

const BillingDashboard = () => {
  const [subscription, setSubscription] = useState(null)
  const [usage, setUsage] = useState(null)
  const [limits, setLimits] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchBillingData()
  }, [])

  const fetchBillingData = async () => {
    try {
      const [subResponse, usageResponse, limitsResponse] = await Promise.all([
        api.get('/billing/current'),
        api.get('/billing/usage'),
        api.get('/billing/limits')
      ])
      
      setSubscription(subResponse.data)
      setUsage(usageResponse.data)
      setLimits(limitsResponse.data.data)
    } catch (error) {
      console.error('Failed to fetch billing data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getUsagePercentage = (current, limit) => {
    if (limit === -1) return 0 // Unlimited
    return Math.min((current / limit) * 100, 100)
  }

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return 'text-red-600'
    if (percentage >= 75) return 'text-yellow-600'
    return 'text-green-600'
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Billing & Usage</h1>
        <p className="text-gray-600 mt-2">Manage your subscription and monitor usage</p>
      </div>

      {/* Subscription Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Plan</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{subscription?.plan || 'Free'}</div>
            <p className="text-xs text-muted-foreground">
              {subscription?.status === 'active' ? (
                <span className="flex items-center text-green-600">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Active
                </span>
              ) : (
                <span className="flex items-center text-red-600">
                  <XCircle className="h-3 w-3 mr-1" />
                  {subscription?.status || 'Inactive'}
                </span>
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Billing Cycle</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {subscription?.billing_cycle || 'Monthly'}
            </div>
            <p className="text-xs text-muted-foreground">
              {subscription?.current_period_end && (
                <>Renews on {formatDate(subscription.current_period_end)}</>
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Usage Period</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Current</div>
            <p className="text-xs text-muted-foreground">
              {usage?.period_start && usage?.period_end && (
                <>
                  {formatDate(usage.period_start)} - {formatDate(usage.period_end)}
                </>
              )}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Usage Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* API Calls */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">API Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-2xl font-bold">{usage?.api_calls || 0}</span>
                <span className="text-sm text-gray-500">
                  / {limits?.limits.api_calls === -1 ? '∞' : limits?.limits.api_calls}
                </span>
              </div>
              {limits?.limits.api_calls !== -1 && (
                <Progress 
                  value={getUsagePercentage(usage?.api_calls || 0, limits?.limits.api_calls)} 
                  className="h-2"
                />
              )}
              <p className={`text-xs ${getUsageColor(getUsagePercentage(usage?.api_calls || 0, limits?.limits.api_calls))}`}>
                {getUsagePercentage(usage?.api_calls || 0, limits?.limits.api_calls).toFixed(1)}% used
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Compute Minutes */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Compute Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-2xl font-bold">{usage?.compute_minutes || 0}m</span>
                <span className="text-sm text-gray-500">
                  / {limits?.limits.compute_minutes === -1 ? '∞' : `${limits?.limits.compute_minutes}m`}
                </span>
              </div>
              {limits?.limits.compute_minutes !== -1 && (
                <Progress 
                  value={getUsagePercentage(usage?.compute_minutes || 0, limits?.limits.compute_minutes)} 
                  className="h-2"
                />
              )}
              <p className={`text-xs ${getUsageColor(getUsagePercentage(usage?.compute_minutes || 0, limits?.limits.compute_minutes))}`}>
                {getUsagePercentage(usage?.compute_minutes || 0, limits?.limits.compute_minutes).toFixed(1)}% used
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Storage */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Storage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-2xl font-bold">{usage?.storage_gb?.toFixed(1) || 0}GB</span>
                <span className="text-sm text-gray-500">
                  / {limits?.limits.storage_gb === -1 ? '∞' : `${limits?.limits.storage_gb}GB`}
                </span>
              </div>
              {limits?.limits.storage_gb !== -1 && (
                <Progress 
                  value={getUsagePercentage(usage?.storage_gb || 0, limits?.limits.storage_gb)} 
                  className="h-2"
                />
              )}
              <p className={`text-xs ${getUsageColor(getUsagePercentage(usage?.storage_gb || 0, limits?.limits.storage_gb))}`}>
                {getUsagePercentage(usage?.storage_gb || 0, limits?.limits.storage_gb).toFixed(1)}% used
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Bandwidth */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Bandwidth</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-2xl font-bold">{usage?.bandwidth_gb?.toFixed(1) || 0}GB</span>
                <span className="text-sm text-gray-500">/ ∞</span>
              </div>
              <p className="text-xs text-green-600">Unlimited</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Plan Features */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Plan Features</CardTitle>
          <CardDescription>
            Features included in your {limits?.plan} plan
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {limits?.features?.map((feature, index) => (
              <div key={index} className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm">{feature}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Usage Warnings */}
      {usage && limits && (
        <div className="space-y-4">
          {Object.entries({
            'API Calls': { current: usage.api_calls, limit: limits.limits.api_calls },
            'Compute Minutes': { current: usage.compute_minutes, limit: limits.limits.compute_minutes },
            'Storage': { current: usage.storage_gb, limit: limits.limits.storage_gb }
          }).map(([resource, data]) => {
            const percentage = getUsagePercentage(data.current, data.limit)
            if (percentage >= 80 && data.limit !== -1) {
              return (
                <motion.div
                  key={resource}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Card className="border-yellow-200 bg-yellow-50">
                    <CardContent className="pt-6">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="h-5 w-5 text-yellow-600" />
                        <div>
                          <p className="font-medium text-yellow-800">
                            {resource} usage is at {percentage.toFixed(1)}%
                          </p>
                          <p className="text-sm text-yellow-600">
                            Consider upgrading your plan to avoid service interruption.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            }
            return null
          })}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-4 mt-8">
        <Button 
          onClick={() => window.location.href = '/pricing'}
          className="flex-1"
        >
          Upgrade Plan
        </Button>
        <Button 
          variant="outline" 
          onClick={fetchBillingData}
          className="flex-1"
        >
          Refresh Data
        </Button>
      </div>
    </div>
  )
}

export default BillingDashboard

