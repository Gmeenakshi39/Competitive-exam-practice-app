import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { BookOpen, Brain, Calculator, CheckCircle2, ChevronRight, CircleHelp, FileDown, GraduationCap, Printer, RefreshCw, Sparkles, Target, Timer, Trophy } from "lucide-react";
import "./styles.css";

const API = "http://127.0.0.1:8000";
const topicMap = {
  "Quantitative Aptitude": ["All topics", "Percentages", "Averages", "Ratio and Proportion", "Profit and Loss", "Simple Interest", "Number Series","Probability", "Time and Work", "Time, Speed and Distance", "Mensuration", "Algebra", "Geometry", "Trigonometry"],
  "Reasoning": ["All topics", "Number Series", "Coding-Decoding", "Analogy", "Blood Relations","Seating Arrangement", "Syllogism", "Direction Sense", "Puzzle", "Logical Venn Diagram", "Data Sufficiency", "Input-Output", "Statement and Conclusion"]
};

function App() {
  const [subject, setSubject] = useState("Quantitative Aptitude");
  const [level, setLevel] = useState("Beginner");
  const [topic, setTopic] = useState("All topics");
  const [count, setCount] = useState(10);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [grading, setGrading] = useState(false);
  const [gradingError, setGradingError] = useState("");
  const [gradeResult, setGradeResult] = useState(null);
  const [error, setError] = useState("");
  const [setId, setSetId] = useState(null);
  const [seed, setSeed] = useState(null);

  const localScore = useMemo(() => questions.reduce((n, q) => n + (answers[q.id] === q.answer ? 1 : 0), 0), [questions, answers]);
  const score = gradeResult?.correct ?? localScore;
  const answeredCount = Object.keys(answers).filter(id => questions.some(q => q.id === id)).length;

  async function generate() {
    setLoading(true); setError(""); setGradingError(""); setGradeResult(null); setSubmitted(false); setShowKey(false); setAnswers({});
    try {
      const response = await fetch(`${API}/api/generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject, level, topic, count: Number(count) })
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Could not generate questions. Check the backend is running.");
      }
      const data = await response.json();
      setQuestions(data.questions); setSeed(data.seed); setSetId(data.setId);
      setTimeout(() => document.getElementById("question-list")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (e) {
      setError(e.message || "Unable to connect to the API. Start the FastAPI backend on port 8000.");
    } finally { setLoading(false); }
  }

  function resetAnswers() { setAnswers({}); setGradeResult(null); setGradingError(""); setSubmitted(false); setShowKey(false); }
  async function submitAnswers() {
    setGrading(true);
    setGradingError("");
    try {
      const response = await fetch(`${API}/api/grade`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers, setId })
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Could not submit your answers.");
      }
      setGradeResult(await response.json());
      setSubmitted(true);
      setShowKey(true);
      setTimeout(() => document.getElementById("score-panel")?.scrollIntoView({behavior:"smooth",block:"center"}), 80);
    } catch (e) {
      setGradingError(e.message || "Unable to save your result. Check that the backend is running.");
    } finally {
      setGrading(false);
    }
  }
  function printWorksheet() { window.print(); }

  return <div className="app-shell">
    <header className="topbar no-print">
      <a className="brand" href="#" aria-label="PrepSprint home"><span className="brand-mark"><GraduationCap size={22}/></span><span>Prep<span className="brand-accent">Sprint</span></span></a>
      <nav><a href="#builder">Practice</a><a href="#question-list">Question set</a><a href="#print-help">Print guide</a></nav>
      <span className="top-tag"><span className="live-dot"/> Free practice</span>
    </header>

    <main>
      <section className="hero no-print">
        <div className="hero-copy">
          <div className="eyebrow"><Sparkles size={14}/> YOUR DAILY EDGE</div>
          <h1>Small steps.<br/><span>Big exam goals.</span></h1>
          <p>Build speed and accuracy for SSC, RRB NTPC and state government exams with fresh aptitude and reasoning practice.</p>
          <div className="hero-pills"><span><CheckCircle2 size={15}/> Randomized questions</span><span><Printer size={15}/> Print-friendly sheets</span></div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="orbit orbit-one"></div><div className="orbit orbit-two"></div>
          <div className="hero-card card-main"><div className="mini-icon"><Target size={20}/></div><div className="mini-label">TODAY'S FOCUS</div><strong>Consistency wins.</strong><div className="progress-track"><div className="progress-fill"></div></div><small>One question at a time</small></div>
          <div className="float-card float-top"><Calculator size={18}/><span>Quant + Reasoning</span></div>
          <div className="float-card float-bottom"><Trophy size={18}/><span>Track your progress</span></div>
        </div>
      </section>

      <section id="builder" className="builder-section">
        <div className="section-heading"><div><div className="eyebrow dark-eyebrow">PRACTICE BUILDER</div><h2>Create your question set</h2><p>Choose your focus. We'll generate a new set with validated answers.</p></div><div className="step-indicator"><span>01</span><i></i><span className="muted-step">02</span><i></i><span className="muted-step">03</span></div></div>
        <div className="builder-card">
          <div className="field-group"><label>SUBJECT</label><div className="choice-grid">
            <button className={`choice-card ${subject === "Quantitative Aptitude" ? "selected" : ""}`} onClick={() => {setSubject("Quantitative Aptitude");setTopic("All topics");resetAnswers();}}><span className="choice-icon purple"><Calculator size={20}/></span><span><strong>Quantitative Aptitude</strong><small>Maths, numbers & calculations</small></span><span className="choice-check">{subject === "Quantitative Aptitude" ? "✓" : ""}</span></button>
            <button className={`choice-card ${subject === "Reasoning" ? "selected" : ""}`} onClick={() => {setSubject("Reasoning");setTopic("All topics");resetAnswers();}}><span className="choice-icon orange"><Brain size={20}/></span><span><strong>Reasoning</strong><small>Logic, patterns & relationships</small></span><span className="choice-check">{subject === "Reasoning" ? "✓" : ""}</span></button>
          </div></div>
          <div className="form-row">
            <div className="field-group"><label htmlFor="topic">TOPIC</label><select id="topic" value={topic} onChange={e => setTopic(e.target.value)}>{topicMap[subject].map(t => <option key={t}>{t}</option>)}</select></div>
            <div className="field-group"><label>DIFFICULTY</label><div className="level-switch">{["Beginner","Intermediate","Advanced"].map(l => <button key={l} className={`level-btn ${level === l ? `active ${l.toLowerCase()}` : ""}`} onClick={() => setLevel(l)}>{l}</button>)}</div></div>
            <div className="field-group count-field"><label htmlFor="count">QUESTIONS</label><select id="count" value={count} onChange={e => setCount(e.target.value)}>{[10,15,30,50,100].map(n => (<option key={n} value={n}>{n} questions</option>))}</select></div>
          </div>
          <div className="builder-footer"><div className="validation-note"><CheckCircle2 size={17}/><span>Every generated question includes a verified answer.</span></div><button className="primary-btn" onClick={generate} disabled={loading || grading}>{loading ? <><RefreshCw className="spin" size={17}/> Generating…</> : <><Sparkles size={17}/> Generate questions <ChevronRight size={17}/></>}</button></div>
        </div>
        {error && <div className="error-box"><CircleHelp size={18}/><div><strong>Couldn't generate your set</strong><p>{error}</p><small>Start the backend using <code>uvicorn app.main:app --reload</code> from the backend folder.</small></div></div>}
      </section>

      {questions.length > 0 && <section id="question-list" className="questions-section">
        <div className="question-header">
          <div><div className="eyebrow dark-eyebrow">YOUR PRACTICE SET</div><h2>{subject} <span className="heading-dot">·</span> {level}</h2><p>{questions.length} questions <span>•</span> {topic} <span>•</span> Fresh set #{String(seed).slice(-5)}</p></div>
          <div className="question-actions no-print"><button className="secondary-btn" onClick={printWorksheet}><Printer size={16}/> Print / PDF</button><button className="icon-btn" onClick={generate} disabled={loading || grading} title="Generate a new set" aria-label="Generate a new set"><RefreshCw size={17}/></button></div>
        </div>
        <div className="practice-toolbar no-print"><div className="toolbar-left"><span className="toolbar-icon"><Timer size={17}/></span><span><strong>Practice mode</strong><small>{answeredCount} of {questions.length} answered</small></span><div className="answer-progress"><span style={{width: `${answeredCount / questions.length * 100}%`}}/></div></div><div className="toolbar-right"><button className="text-btn" onClick={() => setShowKey(v => !v)}>{showKey ? "Hide answer key" : "Show answer key"}</button><button className="text-btn" onClick={resetAnswers} disabled={grading || loading}>Reset answers</button></div></div>
        <div className="question-grid">
          {questions.map((q, index) => {
            const selected = answers[q.id];
            const isCorrect = selected === q.answer;
            return <article className={`question-card ${submitted ? "submitted" : ""}`} key={q.id}>
              <div className="question-meta"><span className="question-number">Q{String(index + 1).padStart(2,"0")}</span><span className="topic-chip">{q.topic}</span></div>
              <h3>{q.prompt}</h3>
              <div className="options-list">{q.options.map((option, i) => {
                const chosen = selected === option;
                const correctOption = submitted && option === q.answer;
                return <button key={`${q.id}-${option}`} disabled={submitted || grading || loading} className={`option ${chosen ? "chosen" : ""} ${correctOption ? "correct-option" : ""} ${submitted && chosen && !isCorrect ? "wrong-option" : ""}`} onClick={() => setAnswers(prev => ({...prev, [q.id]: option}))}><span className="option-letter">{String.fromCharCode(65+i)}</span><span>{option}</span>{correctOption && <CheckCircle2 size={16} className="option-result"/>}</button>
              })}</div>
              {(showKey || submitted) && <div className="explanation"><strong>{submitted ? (isCorrect ? "Correct answer" : `Correct answer: ${q.answer}`) : `Answer: ${q.answer}`}</strong><p>{q.explanation}</p></div>}
            </article>
          })}
        </div>
        <div className="submit-panel no-print"><div><strong>Ready to check your answers?</strong><p>Your score will appear here. You can review explanations after submitting.</p></div><button className="primary-btn" onClick={submitAnswers} disabled={submitted || grading || loading}>{grading ? <><RefreshCw className="spin" size={17}/> Saving…</> : <>Submit answers <ChevronRight size={17}/></>}</button></div>
        {gradingError && <div className="error-box no-print"><CircleHelp size={18}/><div><strong>Couldn't save your result</strong><p>{gradingError}</p></div></div>}
        {submitted && <div id="score-panel" className="score-panel"><div className="score-icon"><Trophy size={25}/></div><div className="score-copy"><span>YOUR RESULT</span><h2>{score} <small>/ {questions.length}</small></h2><p>{score === questions.length ? "Excellent work — a perfect score!" : score / questions.length >= .7 ? "Good progress. Review any missed questions and keep going." : "Every attempt is progress. Review the explanations and try another set."}</p></div><div className="score-ring" style={{"--score": `${score / questions.length * 100}%`}}><div>{Math.round(score / questions.length * 100)}<small>%</small></div></div></div>}
      </section>}

      <section id="print-help" className="print-callout no-print"><div className="print-icon"><FileDown size={23}/></div><div><strong>Make every page count.</strong><p>Print in a compact two-column format. Select “Save as PDF” in your browser's print dialog to keep a digital copy.</p></div><button className="secondary-btn" onClick={printWorksheet}><Printer size={16}/> Print worksheet</button></section>
      <footer className="footer no-print"><a className="brand footer-brand" href="#"><span className="brand-mark"><GraduationCap size={18}/></span><span>Prep<span className="brand-accent">Sprint</span></span></a><span>Practice smart. Prepare with purpose.</span><span className="footer-note">Starter MVP · v0.1</span></footer>
    </main>
  </div>;
}

createRoot(document.getElementById("root")).render(<App />);
