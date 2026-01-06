import { useHealth } from "../../api/hooks";
import MenuBar from "../../components/MenuBar";
import { useApiStatusStore } from "../../state/apiStatusStore";

const ConnectionStatusWindow = () => {
  const health = useHealth();
  const status = useApiStatusStore();

  return (
    <div>
      <MenuBar items={["View", "Help"]} />
      <h3>Connection Status</h3>
      <div>Status: {status.online ? "Online" : "Offline"}</div>
      <div>Last Checked: {status.lastChecked ? new Date(status.lastChecked).toLocaleString() : "Never"}</div>
      {status.lastError && <div>Last Error: {status.lastError}</div>}
      {health.isFetching && <div>Checking...</div>}
    </div>
  );
};

export default ConnectionStatusWindow;
