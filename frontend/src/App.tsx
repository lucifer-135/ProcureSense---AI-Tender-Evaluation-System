import Layout from "./components/Layout";
import TenderUpload from "./pages/TenderUpload";
import CriteriaReview from "./pages/CriteriaReview";
import BidderUpload from "./pages/BidderUpload";
import EvaluationResults from "./pages/EvaluationResults";
import HumanReview from "./pages/HumanReview";
import Report from "./pages/Report";
import { useAppStore } from "./lib/store";

export default function App() {
  const { currentStep, setStep } = useAppStore();

  const navigate = (step: number) => setStep(step);
  const next = () => setStep(currentStep + 1);

  const pages = [
    <TenderUpload onNext={next} />,
    <CriteriaReview onNext={next} />,
    <BidderUpload onNext={next} />,
    <EvaluationResults onNext={next} />,
    <HumanReview onNext={next} />,
    <Report />,
  ];

  return (
    <Layout onNavigate={navigate}>
      {pages[currentStep]}
    </Layout>
  );
}
