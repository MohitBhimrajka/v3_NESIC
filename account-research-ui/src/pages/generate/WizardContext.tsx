import { createContext, useContext, ReactNode } from 'react';
import { useForm, UseFormReturn } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

// Define the form schema
export const wizardFormSchema = z.object({
  targetCompany: z.string().min(2, 'Target company name is required'),
  userCompany: z.string().min(2, 'Your company name is required'),
  language: z.enum(['English', 'Japanese', 'Spanish', 'French', 'German', 'Chinese', 'Portuguese', 'Italian', 'Russian', 'Korean']),
  sections: z.array(z.string()).default([]),
});

// Infer the form values type from the schema
export type FormValues = z.infer<typeof wizardFormSchema>;

// Create the context
type WizardContextType = UseFormReturn<FormValues> & {
  currentStep: number;
  setCurrentStep: (step: number) => void;
  onSubmit: (handler: (data: FormValues) => Promise<void>) => (e: React.FormEvent) => void;
};

const WizardContext = createContext<WizardContextType | null>(null);

// Create the provider
interface WizardProviderProps {
  children: ReactNode;
  defaultValues?: Partial<FormValues>;
  currentStep: number;
  setCurrentStep: (step: number) => void;
  onSubmitHandler?: (data: FormValues) => Promise<void>;
}

export function WizardProvider({
  children,
  defaultValues = {
    language: 'English',
    sections: [],
  },
  currentStep,
  setCurrentStep,
  onSubmitHandler,
}: WizardProviderProps) {
  const methods = useForm<FormValues>({
    resolver: zodResolver(wizardFormSchema),
    defaultValues: {
      ...defaultValues,
      sections: defaultValues.sections || [],
    } as FormValues,
    mode: 'onChange',
  });

  const onSubmit = (handler: (data: FormValues) => Promise<void>) => 
    async (e: React.FormEvent) => {
      e.preventDefault();
      try {
        await methods.handleSubmit(handler)(e);
      } catch (error) {
        console.error('Form submission error:', error);
      }
    };

  return (
    <WizardContext.Provider 
      value={{ 
        ...methods, 
        currentStep, 
        setCurrentStep,
        onSubmit,
      }}
    >
      {children}
    </WizardContext.Provider>
  );
}

// Hook to use the context
export function useWizardForm() {
  const context = useContext(WizardContext);
  if (!context) {
    throw new Error('useWizardForm must be used within a WizardProvider');
  }
  return context;
} 