import Navbar from "~/components/Navbar";
import type { Route } from "./+types/home";
import { resumes } from "../../constants";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "AlignCV" },
    { name: "description", content: "Smart feedback for your resume!" },
  ];
}

export default function Home() {
  return (
    <main className="bg-[url('/images/bg-main.svg')] bg-cover">
      <Navbar />

      <section className="main-section">
        <div className="page-heading">
          <h1>Track You Applications & Resume Ratings</h1>
          <h2>Review your submissions and check AI-powered feedback</h2>
        </div>
      </section>

      {resumes.map((resume) => (
        <div>
          <h1>{resume.jobTitle}</h1>
        </div>
      ))}
    </main>
  );
}
