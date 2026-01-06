import { useState } from "react";
import MenuBar from "../../components/MenuBar";
import Tabs from "../../components/Tabs";
import { useTopicSearch, useTopicDetail } from "../../api/hooks";
import { useDebateStore } from "../../state/debateStore";

const TopicExplorerWindow = () => {
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined);
  const [activeTab, setActiveTab] = useState("Overview");
  const search = useTopicSearch(query);
  const detail = useTopicDetail(selectedId);
  const debate = useDebateStore();

  const results = search.data?.results ?? [];

  return (
    <div>
      <MenuBar items={["File", "Edit", "View", "Help"]} />
      <div className="field-row" style={{ marginBottom: 8 }}>
        <label>
          Search Topics
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="e.g., AI in Education"
          />
        </label>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 8 }}>
        <div className="panel" style={{ maxHeight: 320, overflow: "auto" }}>
          {search.isLoading && <div>Searching...</div>}
            {results.map((topic) => (
              <button
                key={topic.id}
                type="button"
                onClick={() => setSelectedId(topic.id)}
                style={{ display: "block", width: "100%" }}
              >
              <strong>{topic.title}</strong>
              <div>{topic.summary}</div>
            </button>
          ))}
          {results.length === 0 && !search.isLoading && <div>No results yet.</div>}
        </div>
        <div className="panel">
          <Tabs
            tabs={["Overview", "Quick Study"]}
            active={activeTab}
            onChange={setActiveTab}
          />
          {detail.data ? (
            activeTab === "Overview" ? (
              <div>
                <h3>{detail.data.title}</h3>
                <p>{detail.data.description}</p>
                <h4>Sources</h4>
                <ul>
                  {detail.data.sources.map((source) => (
                    <li key={source}>
                      <a href={source} target="_blank" rel="noreferrer">
                        {source}
                      </a>
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  onClick={() => debate.setTopic(detail.data.id, detail.data.title)}
                >
                  Add to Debate
                </button>
              </div>
            ) : (
              <div>
                <h4>Key Points</h4>
                <ul>
                  {detail.data.keyPoints.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
                <h4>Pros</h4>
                <ul>
                  {detail.data.pros.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
                <h4>Cons</h4>
                <ul>
                  {detail.data.cons.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
                <h4>Common Fallacies</h4>
                <ul>
                  {detail.data.fallacies.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
              </div>
            )
          ) : (
            <div>Select a topic to view details.</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TopicExplorerWindow;
