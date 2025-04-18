import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="relative min-h-screen bg-black flex flex-col">
      {/* Animated gradient bar */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-lime via-lime-lt to-lime animate-gradient-x"></div>
      
      {/* Hero content */}
      <div className="flex flex-1 items-center justify-center px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Supercharge your account planning with AI‑driven research.
          </h1>
          <p className="text-blue text-xl md:text-2xl mb-8 max-w-2xl mx-auto">
            Get deeper insights, faster recommendations, and data-backed strategies
            in a fraction of the time.
          </p>
          <Button 
            variant="primary" 
            size="lg"
            onClick={() => navigate('/generate')}
            className="mt-6"
          >
            Start Research
          </Button>
        </div>
      </div>
    </div>
  )
} 