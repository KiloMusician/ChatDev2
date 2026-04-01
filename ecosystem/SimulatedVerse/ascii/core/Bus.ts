import mitt from "mitt";

export type Events = {
  "ascii/toggleBackend": undefined;
  "ascii/toggleHUD": undefined;
  "ascii/switchVantage": undefined;
  "ascii/pause": undefined;
  "ascii/bigRedButton": undefined;
  "ascii/styleToggle": undefined;
  "ascii/refreshView": undefined;
};

export const bus = mitt<Events>();