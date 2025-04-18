import { useWizardForm } from "../WizardContext";

export function AboutYouStep() {
  const { register, formState: { errors } } = useWizardForm();
  
  return (
    <div className="space-y-6">
      <div>
        <label htmlFor="userCompany" className="block text-sm font-medium text-white mb-1">
          Your Company
        </label>
        <input
          id="userCompany"
          type="text"
          className="w-full p-2 rounded-md border-gray-dk bg-navy text-white focus:border-lime focus:outline-none focus:ring-1 focus:ring-lime"
          placeholder="Enter your company name"
          {...register("userCompany")}
        />
        {errors.userCompany && (
          <p className="text-orange text-sm mt-1">{errors.userCompany.message}</p>
        )}
      </div>
      
      <p className="text-gray-lt text-sm">
        Tell us about your company to help personalize the research results and recommendations.
      </p>
    </div>
  );
} 