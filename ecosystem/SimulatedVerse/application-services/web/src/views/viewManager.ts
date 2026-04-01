import { AsciiRenderer } from "./application-services/web/src/render/asciiRenderer.ts";
import { State, setStage } from "./application-services/web/src/engine/state.ts";
import { MicrobeView } from "./application-services/web/src/views/view.microbe.ts";
import { ColonyView } from "./application-services/web/src/views/view.colony.ts";
import { CityView } from "./application-services/web/src/views/view.city.ts";
import { PlanetView } from "./application-services/web/src/views/view.planet.ts";
import { SystemView } from "./application-services/web/src/views/view.system.ts";
import { SpaceView } from "./application-services/web/src/views/view.space.ts";

export interface IView {
  name: string;
  enter(): void;
  exit(): void;
  render(r: AsciiRenderer): void;
  update(dt: number): void;
  input?(k: string): void;
}

export class ViewManager {
  r: AsciiRenderer;
  views: Record<string, IView>;
  current: IView;
  
  constructor(r: AsciiRenderer){
    this.r = r;
    this.views = {
      microbe: new MicrobeView(),
      colony: new ColonyView(),
      city: new CityView(),
      planet: new PlanetView(),
      system: new SystemView(),
      space: new SpaceView()
    };
    this.current = this.views[State.stage];
    this.current.enter();
  }
  
  switch(name: string){
    if(this.current) this.current.exit();
    this.current = this.views[name];
    setStage(name as any);
    this.current.enter();
  }
  
  render(){ this.current.render(this.r); }
  update(dt: number){ this.current.update(dt); }
}