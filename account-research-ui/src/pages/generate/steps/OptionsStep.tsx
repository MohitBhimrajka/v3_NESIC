import { useWizardForm } from "../WizardContext";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../../../components/ui/accordion";
import { Checkbox } from "../../../components/ui/checkbox";

const AVAILABLE_SECTIONS = [
  { id: "overview", label: "Company Overview" },
  { id: "financials", label: "Financial Analysis" },
  { id: "market", label: "Market Position" },
  { id: "competitors", label: "Competitors" },
  { id: "swot", label: "SWOT Analysis" },
  { id: "products", label: "Products & Services" },
  { id: "management", label: "Management Team" },
  { id: "opportunities", label: "Partnership Opportunities" },
];

export function OptionsStep() {
  const { register, watch, setValue, formState: { errors } } = useWizardForm();
  const selectedLanguage = watch("language");
  const selectedSections = watch("sections");
  
  const handleSectionToggle = (sectionId: string) => {
    const currentSections = selectedSections || [];
    const updatedSections = currentSections.includes(sectionId)
      ? currentSections.filter(id => id !== sectionId)
      : [...currentSections, sectionId];
    
    setValue("sections", updatedSections, { shouldValidate: true });
  };
  
  return (
    <div className="space-y-6">
      <div>
        <label htmlFor="language" className="block text-sm font-medium text-white mb-1">
          Language
        </label>
        <select
          id="language"
          className="w-full p-2 rounded-md border-gray-dk bg-navy text-white focus:border-lime focus:outline-none focus:ring-1 focus:ring-lime"
          {...register("language")}
        >
          <option value="English">English</option>
          <option value="Japanese">Japanese</option>
          <option value="Spanish">Spanish</option>
          <option value="French">French</option>
          <option value="German">German</option>
          <option value="Chinese">Chinese</option>
          <option value="Portuguese">Portuguese</option>
          <option value="Italian">Italian</option>
          <option value="Russian">Russian</option>
          <option value="Korean">Korean</option>
        </select>
        {errors.language && (
          <p className="text-orange text-sm mt-1">{errors.language.message}</p>
        )}
      </div>
      
      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="advanced">
          <AccordionTrigger className="text-white">Advanced Options</AccordionTrigger>
          <AccordionContent>
            <div className="space-y-4">
              <p className="text-gray-lt text-sm">Select the sections to include in your report:</p>
              
              <div className="space-y-3">
                {AVAILABLE_SECTIONS.map((section) => (
                  <div key={section.id} className="flex items-center space-x-2">
                    <Checkbox 
                      id={section.id}
                      checked={selectedSections?.includes(section.id)}
                      onCheckedChange={() => handleSectionToggle(section.id)}
                    />
                    <label
                      htmlFor={section.id}
                      className="text-sm font-medium leading-none text-white peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      {section.label}
                    </label>
                  </div>
                ))}
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
} 