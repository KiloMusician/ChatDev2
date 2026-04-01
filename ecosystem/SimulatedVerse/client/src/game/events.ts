import mitt from "mitt";
type Ev = {
  "breath:tick": { dt:number, t:number };
  "receipt": any;
  "ui:flash": string;
};
export const bus = mitt<Ev>();
export const emitReceipt = (r:any)=> bus.emit("receipt", r);