import { useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { AlertTriangle, ShieldAlert, Building2, Layers, Tags } from 'lucide-react'
import VoiceAgent from '../components/VoiceAgent'
import TabPanel from '../components/TabPanel'
import StackCard from '../components/StackCard'
import GapCard from '../components/GapCard'
import ToolCard from '../components/ToolCard'
import CallStatusTab from '../components/CallStatusTab'
import useAnalysisVoice from '../hooks/useAnalysisVoice'
import { Card, CardContent } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import type { RepoResponse, TechStack, Tool, Recommendation } from '../types/api'

interface BookingState {
  toolId: string
  toolName: string
  bookingId: string
}

async function fetchRepo(repoId: string): Promise<RepoResponse> {
  const res = await fetch(`/api/repos/${repoId}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to load analysis')
  }
  return res.json()
}

async function fetchRecommendations(repoId: string): Promise<Recommendation[]> {
  const res = await fetch(`/api/repos/${repoId}/recommendations`)
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Failed to fetch recommendations')
  }
  return res.json()
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0 },
}

export default function AnalysisPage() {
  const { repo_id } = useParams<{ repo_id: string }>()
  const [activeTab, setActiveTab] = useState<'stack' | 'recommendations' | 'call'>('stack')
  const [bookingState, setBookingState] = useState<BookingState | null>(null)

  const { data: repoData, isLoading: repoLoading, error: repoError } = useQuery({
    queryKey: ['repo', repo_id],
    queryFn: () => fetchRepo(repo_id!),
    enabled: !!repo_id,
    staleTime: 5 * 60 * 1000,
  })

  const { data: recommendations = [], isLoading: recsLoading } = useQuery({
    queryKey: ['recommendations', repo_id],
    queryFn: () => fetchRecommendations(repo_id!),
    enabled: !!repo_id,
    staleTime: 5 * 60 * 1000,
  })

  const { status, isSpeaking, messages, startCall, endCall } = useAnalysisVoice({ autoStart: false })

  const handleBookDemo = useCallback(async (tool: Tool) => {
    try {
      const res = await fetch('/api/booking/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_type: 'software_demo',
          notes: `Demo for ${tool.name}`,
        }),
      })

      if (!res.ok) throw new Error('Failed to create booking')

      const booking = await res.json()

      const callRes = await fetch(`/api/booking/${booking.id}/call`, {
        method: 'POST',
      })

      if (!callRes.ok) throw new Error('Failed to start call')

      setBookingState({
        toolId: tool.id,
        toolName: tool.name,
        bookingId: booking.id,
      })
      setActiveTab('call')
    } catch (err) {
      console.error('Booking error:', err)
    }
  }, [])

  const tabs = [
    { id: 'stack', label: 'Tech Stack' },
    { id: 'recommendations', label: 'Recommendations' },
    ...(bookingState ? [{ id: 'call', label: 'Call Status' }] : []),
  ]

  if (repoLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Spinner className="h-12 w-12 text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading analysis...</p>
        </div>
      </div>
    )
  }

  if (repoError) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-4">
            {repoError instanceof Error ? repoError.message : 'Something went wrong'}
          </p>
          <Link to="/" className="text-primary hover:underline">
            Go back home
          </Link>
        </div>
      </div>
    )
  }

  const fingerprint = repoData!.fingerprint
  const stackCategories = Object.entries(fingerprint.stack) as [keyof TechStack, string[]][]

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="min-h-screen bg-background"
    >
      <div className="flex h-screen">
        {/* Left panel - Voice Agent (~40%) */}
        <div className="w-2/5 border-r border-border p-6 flex flex-col">
          <div className="mb-4">
            <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
              ← Back to Home
            </Link>
          </div>

          <h1 className="text-2xl font-bold text-foreground mb-2">Stack Analysis</h1>
          <p className="text-sm text-muted-foreground mb-6">
            {fingerprint.recommendations_context}
          </p>

          {/* Project Context Badges */}
          {(fingerprint.industry || fingerprint.project_type) && (
            <div className="flex flex-wrap gap-2 mb-4">
              {fingerprint.industry && fingerprint.industry !== 'general' && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <Building2 className="size-3" />
                  {fingerprint.industry}
                </Badge>
              )}
              {fingerprint.project_type && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <Layers className="size-3" />
                  {fingerprint.project_type.replace('_', ' ')}
                </Badge>
              )}
            </div>
          )}

          {/* Keywords */}
          {fingerprint.keywords && fingerprint.keywords.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
                <Tags className="size-3" />
                <span>Keywords</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {fingerprint.keywords.slice(0, 8).map((kw, i) => (
                  <Badge key={i} variant="outline" className="text-xs font-normal">
                    {kw}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <VoiceAgent
            status={status}
            isSpeaking={isSpeaking}
            messages={messages}
            onStart={startCall}
            onEnd={endCall}
          />
        </div>

        {/* Right panel - Tabbed content (~60%) */}
        <div className="w-3/5 p-6 overflow-hidden flex flex-col">
          <TabPanel
            tabs={tabs}
            activeTab={activeTab}
            onTabChange={(id) => setActiveTab(id as typeof activeTab)}
          >
            {/* Tech Stack Tab */}
            {activeTab === 'stack' && (
              <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="show"
                className="space-y-6"
              >
                {/* Complexity Score */}
                <motion.div variants={itemVariants}>
                  <Card>
                    <CardContent>
                      <h2 className="text-lg font-semibold text-card-foreground mb-3">Complexity Score</h2>
                      <div className="flex items-center gap-4">
                        <Progress value={fingerprint.complexity_score * 10} className="flex-1 h-3" />
                        <span className="text-2xl font-bold text-primary">{fingerprint.complexity_score}/10</span>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>

                {/* Stack Categories */}
                <motion.div variants={itemVariants}>
                  <h2 className="text-lg font-semibold text-foreground mb-3">Tech Stack</h2>
                  <div className="grid gap-4 md:grid-cols-2">
                    {stackCategories.map(([category, technologies]) => (
                      <StackCard key={category} category={category} technologies={technologies} />
                    ))}
                  </div>
                </motion.div>

                {/* Use Cases */}
                {fingerprint.use_cases && fingerprint.use_cases.length > 0 && (
                  <motion.div variants={itemVariants}>
                    <Card>
                      <CardContent>
                        <h2 className="text-lg font-semibold text-card-foreground mb-3">Use Cases</h2>
                        <ul className="space-y-2">
                          {fingerprint.use_cases.map((uc, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <span className="text-primary">•</span>
                              {uc}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  </motion.div>
                )}

                {/* Gaps & Risk Flags in Accordion */}
                <motion.div variants={itemVariants}>
                  <Accordion type="multiple" defaultValue={['gaps', 'risks']} className="space-y-2">
                    {/* Gaps */}
                    {fingerprint.gaps.length > 0 && (
                      <AccordionItem value="gaps" className="border rounded-lg px-4">
                        <AccordionTrigger className="hover:no-underline">
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="size-4 text-warning" />
                            <span className="font-semibold">Gaps & Missing Practices</span>
                            <span className="text-xs text-muted-foreground ml-2">({fingerprint.gaps.length})</span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent>
                          <div className="space-y-3">
                            {fingerprint.gaps.map((gap, i) => (
                              <GapCard key={i} description={gap} severity="medium" />
                            ))}
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    )}

                    {/* Risk Flags */}
                    {fingerprint.risk_flags.length > 0 && (
                      <AccordionItem value="risks" className="border rounded-lg px-4">
                        <AccordionTrigger className="hover:no-underline">
                          <div className="flex items-center gap-2">
                            <ShieldAlert className="size-4 text-destructive" />
                            <span className="font-semibold">Risk Flags</span>
                            <span className="text-xs text-muted-foreground ml-2">({fingerprint.risk_flags.length})</span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent>
                          <div className="space-y-3">
                            {fingerprint.risk_flags.map((flag, i) => (
                              <GapCard key={i} description={flag} severity="high" />
                            ))}
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    )}
                  </Accordion>
                </motion.div>
              </motion.div>
            )}

            {/* Recommendations Tab */}
            {activeTab === 'recommendations' && (
              <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="show"
                className="space-y-4"
              >
                {recsLoading && (
                  <div className="text-center py-12">
                    <Spinner className="h-8 w-8 text-primary mx-auto" />
                    <p className="mt-4 text-muted-foreground">Loading recommendations...</p>
                  </div>
                )}

                {!recsLoading && recommendations.length === 0 && (
                  <div className="bg-muted border border-border rounded-lg p-8 text-center">
                    <p className="text-muted-foreground">No recommendations found.</p>
                  </div>
                )}

                {!recsLoading && recommendations.map((rec) => (
                  <motion.div key={rec.tool.id} variants={itemVariants}>
                    <ToolCard
                      tool={rec.tool}
                      suitabilityScore={rec.suitability_score}
                      demoPriority={rec.demo_priority}
                      explanation={rec.explanation}
                      matchReasons={rec.match_reasons}
                      onBookDemo={() => handleBookDemo(rec.tool)}
                    />
                  </motion.div>
                ))}
              </motion.div>
            )}

            {/* Call Status Tab */}
            {activeTab === 'call' && bookingState && (
              <CallStatusTab
                booking={bookingState}
                onComplete={() => {
                  // Optionally switch back to recommendations
                }}
              />
            )}
          </TabPanel>
        </div>
      </div>
    </motion.div>
  )
}
