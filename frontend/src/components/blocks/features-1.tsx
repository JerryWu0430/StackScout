import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Link2, Mic, Sparkles } from 'lucide-react'
import { type ReactNode } from 'react'

export function Features1() {
  return (
    <section className="bg-zinc-50 pt-0 pb-16 md:pb-32 dark:bg-transparent">
      <div className="@container mx-auto max-w-5xl px-6">
        <div className="@min-4xl:max-w-full @min-4xl:grid-cols-3 mx-auto mt-4 grid max-w-sm gap-6 *:text-center sm:max-w-none sm:grid-cols-3">
          <Card className="group h-60 shadow-black-950/5">
            <CardHeader className="pb-3">
              <CardDecorator>
                <Link2 className="size-6" aria-hidden />
              </CardDecorator>
              <h3 className="mt-0 font-medium">Paste GitHub URL</h3>
            </CardHeader>
          </Card>

          <Card className="group h-60 shadow-black-950/5">
            <CardHeader className="pb-3">
              <CardDecorator>
                <Mic className="size-6" aria-hidden />
              </CardDecorator>
              <h3 className="mt-0 font-medium">Voice Analysis</h3>
            </CardHeader>
          </Card>

          <Card className="group h-60 shadow-black-950/5">
            <CardHeader className="pb-3">
              <CardDecorator>
                <Sparkles className="size-6" aria-hidden />
              </CardDecorator>
              <h3 className="mt-0 font-medium">Get Stacked.</h3>
            </CardHeader>

          </Card>
        </div>
      </div>
    </section>
  )
}

function CardDecorator({ children }: { children: ReactNode }) {
  return (
    <div
      aria-hidden
      className="relative mx-auto size-36 [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,#000_70%,transparent_100%)]"
    >
      <div
        className="absolute inset-0 [--border:black] dark:[--border:white] bg-[linear-gradient(to_right,var(--border)_1px,transparent_1px),linear-gradient(to_bottom,var(--border)_1px,transparent_1px)] bg-[size:24px_24px] opacity-10"
      />
      <div className="bg-background absolute inset-0 m-auto flex size-12 items-center justify-center border-t border-l">
        {children}
      </div>
    </div>
  )
}
