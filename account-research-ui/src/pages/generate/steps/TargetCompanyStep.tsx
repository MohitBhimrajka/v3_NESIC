import { useWizardForm } from "../WizardContext";

export function TargetCompanyStep() {
  const { register, formState: { errors } } = useWizardForm();
  
  return (
    <div className="space-y-6">
      <div>
        <label htmlFor="targetCompany" className="block text-sm font-medium text-white mb-1">
          Target Company
        </label>
        <input
          id="targetCompany"
          type="text"
          className="w-full p-2 rounded-md border-gray-dk bg-navy text-white focus:border-lime focus:outline-none focus:ring-1 focus:ring-lime"
          placeholder="Enter target company name"
          {...register("targetCompany")}
        />
        {errors.targetCompany && (
          <p className="text-orange text-sm mt-1">{errors.targetCompany.message}</p>
        )}
      </div>
      
      <p className="text-gray-lt text-sm">
        Enter the name of the company you want to research. We'll use this information to generate a comprehensive report.
      </p>
    </div>
  );
} 