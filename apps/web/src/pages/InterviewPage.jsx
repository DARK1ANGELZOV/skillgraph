import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../lib/api";

const DEFAULT_ANSWER_LIMIT = 180;

export function InterviewPage() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answerText, setAnswerText] = useState("");
  const [startAt, setStartAt] = useState(Date.now());
  const [timeLeft, setTimeLeft] = useState(DEFAULT_ANSWER_LIMIT);
  const [speechMetrics, setSpeechMetrics] = useState(null);
  const [error, setError] = useState("");
  const [doneScore, setDoneScore] = useState(null);
  const [phase, setPhase] = useState("interview");
  const [tests, setTests] = useState([]);
  const [testAnswers, setTestAnswers] = useState({});
  const [submittedTests, setSubmittedTests] = useState({});
  const [suspiciousCount, setSuspiciousCount] = useState(0);
  const [recording, setRecording] = useState(false);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);

  const question = useMemo(() => data?.questions?.[currentIndex] ?? null, [data, currentIndex]);
  const allTestsSubmitted = tests.length > 0 && tests.every((test) => submittedTests[test.id]);

  const sendEvent = useCallback(
    async (eventType, severity = "medium", details = {}) => {
      try {
        await api(`/interviews/public/${token}/events`, {
          method: "POST",
          body: JSON.stringify({
            event_type: eventType,
            severity,
            question_id: question?.id ?? null,
            details
          })
        });
        if (severity === "high" || severity === "medium") {
          setSuspiciousCount((value) => value + 1);
        }
      } catch {
        // Do not block interview flow on telemetry failure.
      }
    },
    [question?.id, token]
  );

  const fetchTests = useCallback(async () => {
    const payload = await api(`/interviews/public/${token}/tests`);
    setTests(payload);
    setPhase("tests");
  }, [token]);

  useEffect(() => {
    api(`/interviews/public/${token}`)
      .then((payload) => {
        setData(payload);
        setStartAt(Date.now());
        setTimeLeft(payload.questions?.[0]?.time_limit_sec ?? DEFAULT_ANSWER_LIMIT);
      })
      .catch((err) => setError(err.message));
  }, [token]);

  useEffect(() => {
    if (!question || phase !== "interview") {
      return;
    }
    setTimeLeft(question.time_limit_sec ?? DEFAULT_ANSWER_LIMIT);
    setStartAt(Date.now());
  }, [question?.id, phase]);

  useEffect(() => {
    if (!question || phase !== "interview") {
      return undefined;
    }

    const timer = setInterval(() => {
      setTimeLeft((value) => {
        if (value <= 1) {
          clearInterval(timer);
          void sendEvent("answer_timeout", "high", { question_id: question.id });
          void submitAnswerAutomatically();
          return 0;
        }
        return value - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [question?.id, phase, sendEvent]);

  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === "hidden") {
        void sendEvent("tab_switched", "high", { visibility: "hidden" });
      }
    };
    const onBlur = () => void sendEvent("window_blur", "medium");

    window.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("blur", onBlur);
    return () => {
      window.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("blur", onBlur);
    };
  }, [sendEvent]);

  async function submitAnswerAutomatically() {
    if (!question) {
      return;
    }
    const text = answerText.trim() || "No answer submitted within time limit.";
    await submitAnswerPayload(text);
  }

  async function submitAnswerPayload(text) {
    await api(`/interviews/public/${token}/answers`, {
      method: "POST",
      body: JSON.stringify({
        question_id: question.id,
        text,
        source_type: speechMetrics ? "speech" : "text",
        duration_sec: Math.max(1, Math.floor((Date.now() - startAt) / 1000)),
        stt_confidence: speechMetrics?.confidence ?? null,
        speech_pause_ratio: speechMetrics?.pause_ratio ?? null,
        filler_word_ratio: speechMetrics?.filler_ratio ?? null,
        instability_score: speechMetrics?.instability_score ?? null
      })
    });

    setAnswerText("");
    setSpeechMetrics(null);
    const nextIndex = currentIndex + 1;
    if (data?.questions && nextIndex < data.questions.length) {
      setCurrentIndex(nextIndex);
      return;
    }
    await fetchTests();
  }

  async function submitAnswer(event) {
    event.preventDefault();
    if (!question || !answerText.trim()) {
      return;
    }
    try {
      const suspicious = detectTemplateAnswer(answerText);
      if (suspicious) {
        await sendEvent("template_answer_detected", "medium", { reason: suspicious });
      }
      await submitAnswerPayload(answerText.trim());
    } catch (err) {
      setError(err.message);
    }
  }

  async function completeInterview() {
    try {
      const score = await api(`/interviews/public/${token}/complete`, { method: "POST" });
      setDoneScore(score);
      setPhase("done");
    } catch (err) {
      setError(err.message);
    }
  }

  async function playAudio() {
    if (!question) {
      return;
    }
    try {
      let audioBase64 = question.audio_base64;
      if (!audioBase64) {
        const payload = await api(`/interviews/public/${token}/questions/${question.id}/tts`, {
          method: "POST",
          body: JSON.stringify({ speech_rate: 1.0 })
        });
        audioBase64 = payload.audio_base64;
        setData((prev) => {
          if (!prev) {
            return prev;
          }
          return {
            ...prev,
            questions: prev.questions.map((item) =>
              item.id === question.id ? { ...item, audio_base64: audioBase64 } : item
            )
          };
        });
      }
      if (audioBase64) {
        const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
        await audio.play();
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function transcribeBlob(blob) {
    const audioBase64 = await blobToBase64(blob);
    const payload = await api(`/interviews/public/${token}/stt`, {
      method: "POST",
      body: JSON.stringify({ audio_base64: audioBase64, language: "ru" })
    });
    setSpeechMetrics(payload);
    setAnswerText((prev) => `${prev} ${payload.text}`.trim());
  }

  async function toggleRecording() {
    try {
      if (recording && recorderRef.current) {
        recorderRef.current.stop();
        setRecording(false);
        return;
      }
      const media = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(media);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await transcribeBlob(blob);
        media.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      recorderRef.current = recorder;
      setRecording(true);
      await sendEvent("microphone_recording_started", "low");
    } catch (err) {
      setError(err.message);
    }
  }

  async function submitTest(test) {
    const answers = test.questions.map((item) => ({
      question_id: item.id,
      selected_option: Number(testAnswers[test.id]?.[item.id] ?? -1)
    }));
    try {
      const result = await api(`/interviews/public/${token}/tests/${test.id}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers })
      });
      setSubmittedTests((prev) => ({ ...prev, [test.id]: result }));
    } catch (err) {
      setError(err.message);
    }
  }

  if (error) {
    return (
      <main className="candidate-shell">
        <div className="panel error-box">{error}</div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="candidate-shell">
        <div className="panel">Loading interview...</div>
      </main>
    );
  }

  if (phase === "done" && doneScore) {
    return (
      <main className="candidate-shell">
        <section className="panel">
          <h2>Interview completed</h2>
          <p>Thank you. HR already received your scoring profile and executive summary.</p>
          <div className="score-grid">
            <Score label="Technical" value={doneScore.technical_score} />
            <Score label="Soft skills" value={doneScore.soft_skills_score} />
            <Score label="Logic" value={doneScore.logic_score} />
            <Score label="Psy stability" value={doneScore.psychological_stability_score} />
            <Score label="Nervousness" value={doneScore.nervousness_score} />
            <Score label="Overall" value={doneScore.overall_score} />
          </div>
          <p>
            Recommendation: <strong>{doneScore.recommendation}</strong>
          </p>
        </section>
      </main>
    );
  }

  if (phase === "tests") {
    return (
      <main className="candidate-shell">
        <section className="panel">
          <h2>Candidate Testing</h2>
          <p>Complete all technical, soft skills and psychological assessments to finish the interview.</p>

          {tests.map((test) => (
            <article className="test-card" key={test.id}>
              <header>
                <h3>{test.title}</h3>
                <span>{Math.round(test.duration_sec / 60)} min</span>
              </header>
              {test.questions.map((item) => (
                <div key={item.id} className="test-question">
                  <p>{item.text}</p>
                  <div className="option-grid">
                    {item.options.map((option, optionIndex) => (
                      <label key={`${item.id}-${optionIndex}`}>
                        <input
                          type="radio"
                          name={`${test.id}-${item.id}`}
                          value={optionIndex}
                          onChange={(event) =>
                            setTestAnswers((prev) => ({
                              ...prev,
                              [test.id]: { ...(prev[test.id] ?? {}), [item.id]: Number(event.target.value) }
                            }))
                          }
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
              <button className="secondary-btn" type="button" onClick={() => submitTest(test)}>
                {submittedTests[test.id] ? `Submitted (${submittedTests[test.id].normalized_score.toFixed(1)}%)` : "Submit test"}
              </button>
            </article>
          ))}

          <button className="primary-btn" type="button" disabled={!allTestsSubmitted} onClick={completeInterview}>
            Finish and submit
          </button>
        </section>
      </main>
    );
  }

  if (!question) {
    return (
      <main className="candidate-shell">
        <section className="panel">
          <h2>Loading tests...</h2>
        </section>
      </main>
    );
  }

  return (
    <main className="candidate-shell">
      <section className="panel">
        <header className="question-header">
          <span>
            Candidate: <strong>{data.candidate_name}</strong>
          </span>
          <span>
            Question {currentIndex + 1}/{data.questions.length}
          </span>
        </header>
        <div className="chip-row">
          <span className={`chip ${timeLeft < 30 ? "warning" : ""}`}>Time left: {timeLeft}s</span>
          <span className="chip">Suspicious events: {suspiciousCount}</span>
          <span className="chip">Type: {question.question_type}</span>
        </div>

        <h2>{question.text}</h2>
        <div className="actions-row">
          <button className="secondary-btn" onClick={playAudio} type="button">
            Play voice prompt
          </button>
          <button className="secondary-btn" onClick={toggleRecording} type="button">
            {recording ? "Stop recording" : "Record answer"}
          </button>
        </div>

        <form onSubmit={submitAnswer} className="answer-form">
          <textarea
            placeholder="Type your answer"
            value={answerText}
            onChange={(event) => setAnswerText(event.target.value)}
            onCopy={() => sendEvent("copy_detected", "high")}
            onPaste={() => sendEvent("paste_detected", "high")}
            required
          />
          {speechMetrics ? (
            <div className="speech-metrics">
              STT confidence {Math.round(speechMetrics.confidence * 100)}%, pauses {Math.round(speechMetrics.pause_ratio * 100)}%, fillers{" "}
              {Math.round(speechMetrics.filler_ratio * 100)}%
            </div>
          ) : null}
          <button className="primary-btn" type="submit">
            Submit answer
          </button>
        </form>
      </section>
    </main>
  );
}

function Score({ label, value }) {
  return (
    <article>
      <p>{label}</p>
      <strong>{value}%</strong>
    </article>
  );
}

function detectTemplateAnswer(text) {
  const lower = text.toLowerCase();
  if (lower.includes("as an ai language model")) {
    return "ai_phrase";
  }
  if (text.length > 900 && !/[.!?]/.test(text)) {
    return "long_monologue";
  }
  return "";
}

async function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const value = String(reader.result || "");
      const encoded = value.includes(",") ? value.split(",")[1] : value;
      resolve(encoded);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}
