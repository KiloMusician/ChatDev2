declare module 'jsonwebtoken' {
  const jwt: any;
  export default jwt;
}

declare module '@apollo/federation' {
  export const buildFederatedSchema: any;
}

declare module 'apollo-server-express' {
  export class ApolloServer {
    constructor(config: any);
  }
}

declare module 'apollo-server-core' {
  export const gql: any;
}
