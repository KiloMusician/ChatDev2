import { routeAction } from "../modules/culture_ship/guards/route_enforcer.js";

export async function bootstrapCultureShip() {
  await routeAction({ 
    actor:"system", 
    intent:"bootstrap", 
    costPreference:"zero" 
  });
  console.log("⛭ Culture-Ship bootstrap complete");
}