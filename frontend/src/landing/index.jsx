import { lazy, Suspense } from "react";

const Landing = lazy(() => import(/* webpackChunkName: "landing" */ "./Landing"));
const About = lazy(() => import(/* webpackChunkName: "landing-about" */ "./About"));

const Blank = () => <div className="min-h-screen bg-[#D6D3CA]" data-testid="landing-route-loading" />;

export function LandingPage() {
  return (
    <Suspense fallback={<Blank />}>
      <Landing />
    </Suspense>
  );
}

const Research = lazy(() => import(/* webpackChunkName: "landing-research" */ "./Research"));

export function ResearchPage() {
  return (
    <Suspense fallback={<Blank />}>
      <Research />
    </Suspense>
  );
}

export function AboutPage() {
  return (
    <Suspense fallback={<Blank />}>
      <About />
    </Suspense>
  );
}
