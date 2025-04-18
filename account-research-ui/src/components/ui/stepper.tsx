import * as React from "react"
import { cn } from "../../lib/utils"

export interface StepperProps extends React.HTMLAttributes<HTMLDivElement> {
  steps: {
    id: string;
    label: string;
    description?: string;
  }[];
  activeStep: number;
  orientation?: "horizontal" | "vertical";
}

const Stepper = React.forwardRef<HTMLDivElement, StepperProps>(
  ({ className, steps, activeStep, orientation = "horizontal", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "flex",
          orientation === "vertical" ? "flex-col" : "flex-row",
          className
        )}
        {...props}
      >
        {steps.map((step, index) => {
          const isActive = index === activeStep;
          const isCompleted = index < activeStep;
          
          return (
            <div
              key={step.id}
              className={cn(
                "flex",
                orientation === "vertical" ? "flex-row items-start" : "flex-col items-center",
                index !== steps.length - 1 && orientation === "horizontal" && "flex-1"
              )}
            >
              <div
                className={cn(
                  "flex",
                  orientation === "vertical" ? "flex-col items-center" : "w-full flex-row items-center"
                )}
              >
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium",
                    isCompleted 
                      ? "bg-lime text-white" 
                      : isActive 
                        ? "bg-lime-lt text-navy border-2 border-lime" 
                        : "bg-gray-dk text-white"
                  )}
                >
                  {isCompleted ? (
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-check">
                      <path d="M20 6 9 17l-5-5"/>
                    </svg>
                  ) : (
                    index + 1
                  )}
                </div>

                {index !== steps.length - 1 && (
                  <div
                    className={cn(
                      orientation === "vertical" 
                        ? "h-10 w-px my-1 ml-4"
                        : "h-px w-full mx-1",
                      isCompleted ? "bg-lime" : "bg-gray-dk"
                    )}
                  />
                )}
              </div>

              <div
                className={cn(
                  "flex flex-col",
                  orientation === "vertical" ? "ml-3" : "mt-2"
                )}
              >
                <span
                  className={cn(
                    "text-sm font-medium",
                    isActive || isCompleted ? "text-white" : "text-gray-lt"
                  )}
                >
                  {step.label}
                </span>
                {step.description && (
                  <span className="text-xs text-gray-lt">
                    {step.description}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    )
  }
)

Stepper.displayName = "Stepper"

export { Stepper } 