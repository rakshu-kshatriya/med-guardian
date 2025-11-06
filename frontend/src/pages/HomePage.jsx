import React from 'react';
import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="space-y-6">
      <div className="card-gradient rounded-2xl p-8">
        <h1 className="text-3xl md:text-4xl font-extrabold mb-2">MedGuardian — AI-powered disease outbreak predictor</h1>
        <p className="text-base md:text-lg text-gray-300 max-w-3xl">MedGuardian uses real-time social media and news signals, combined with historical trends, to predict disease outbreaks up to 30 days ahead. Our models (Prophet with robust fallbacks) provide easy-to-understand forecasts and actionable advisories for public health teams and citizens.</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/prediction" className="btn-primary">View 30-day Forecast</Link>
          <Link to="/trends" className="px-4 py-3 rounded-lg border border-white/10 text-white hover:bg-white/5 transition">Explore Trends & Maps</Link>
          <Link to="/data-sources" className="px-4 py-3 rounded-lg border border-white/10 text-white hover:bg-white/5 transition">Data Sources</Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card-gradient rounded-2xl p-6">
          <h3 className="text-lg font-semibold mb-2">Why MedGuardian?</h3>
          <ul className="list-disc list-inside text-gray-300 space-y-2">
            <li>Real-time social & news signals combined with epidemiological forecasting.</li>
            <li>30-day forward predictions with confidence intervals.</li>
            <li>Lightweight, works offline with synthetic fallbacks for testing.</li>
          </ul>
        </div>

        <div className="card-gradient rounded-2xl p-6">
          <h3 className="text-lg font-semibold mb-2">Advantages</h3>
          <ul className="list-disc list-inside text-gray-300 space-y-2">
            <li>Actionable advisories and KPIs for decision makers.</li>
            <li>Map-based routing and disease highlighting for local response.</li>
            <li>Telemetry and Prometheus metrics for observability.</li>
          </ul>
        </div>

        <div className="card-gradient rounded-2xl p-6">
          <h3 className="text-lg font-semibold mb-2">Contact</h3>
          <p className="text-gray-300">Rakshith Akshatriya</p>
          <p className="text-gray-300">Email: <a href="mailto:rakshithakshatriya68@gmail.com" className="underline">rakshithakshatriya68@gmail.com</a></p>
          <p className="text-gray-300">Phone: <a href="tel:+917019942091" className="underline">+91 70199 42091</a></p>
        </div>
      </div>
    </div>
  );
}
