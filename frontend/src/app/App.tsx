import { useEffect } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import Desktop from "../components/Desktop";
import { queryClient } from "./queryClient";
import ToastContainer from "../components/ToastContainer";
import DialogHost from "../components/DialogHost";
import { initializeTheme } from "../state/themeStore";
import { initializeAiTheme } from "../theme";

const App = () => {
  // Initialize themes on first mount
  useEffect(() => {
    initializeTheme();
    initializeAiTheme();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <Desktop />
      <ToastContainer />
      <DialogHost />
    </QueryClientProvider>
  );
};

export default App;
