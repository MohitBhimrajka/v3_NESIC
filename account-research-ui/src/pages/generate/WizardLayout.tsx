import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { WizardProvider, type FormValues } from './WizardContext';
import { Stepper } from '../../components/ui/stepper';
import { Button } from '../../components/ui/button';
import { TargetCompanyStep } from './steps/TargetCompanyStep';
import { AboutYouStep } from './steps/AboutYouStep';
import { OptionsStep } from './steps/OptionsStep';
import api from '../../api/client';
import { useWizardForm } from './WizardContext';

const steps = [
  { id: 'target', label: 'Target company' },
  { id: 'about', label: 'About you' },
  { id: 'options', label: 'Language & options' },
];

// Internal component with access to form context
function WizardForm() {
  const navigate = useNavigate();
  const { onSubmit, formState, currentStep, setCurrentStep } = useWizardForm();
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };
  
  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };
  
  const handleSubmit = async (data: FormValues) => {
    setIsSubmitting(true);
    try {
      const { task_id } = await api.createTask(data);
      navigate(`/task/${task_id}`);
    } catch (error) {
      console.error('Error creating task:', error);
      setIsSubmitting(false);
    }
  };
  
  const stepComponents = [
    <TargetCompanyStep key="target" />,
    <AboutYouStep key="about" />,
    <OptionsStep key="options" />,
  ];
  
  return (
    <form onSubmit={onSubmit(handleSubmit)} className="space-y-8">
      <div className="min-h-[300px]">
        {stepComponents[currentStep]}
      </div>
      
      <div className="flex justify-between pt-4">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={currentStep === 0}
          type="button"
        >
          Back
        </Button>
        
        {currentStep < steps.length - 1 ? (
          <Button
            variant="primary"
            type="button"
            onClick={handleNext}
            disabled={!formState.isValid}
          >
            Next
          </Button>
        ) : (
          <Button
            variant="primary"
            type="submit"
            disabled={!formState.isValid || isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Submit'}
          </Button>
        )}
      </div>
    </form>
  );
}

// Main layout component
export default function WizardLayout() {
  const [currentStep, setCurrentStep] = useState(0);
  
  return (
    <div className="min-h-screen bg-black p-4 md:p-8">
      <div className="max-w-3xl mx-auto bg-navy rounded-2xl shadow-lg p-6 md:p-8">
        <h1 className="text-2xl font-bold text-white mb-6">Create Account Research</h1>
        
        <Stepper 
          steps={steps} 
          activeStep={currentStep} 
          className="mb-8"
        />
        
        <WizardProvider currentStep={currentStep} setCurrentStep={setCurrentStep}>
          <WizardForm />
        </WizardProvider>
      </div>
    </div>
  );
} 