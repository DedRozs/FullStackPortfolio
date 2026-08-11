/* Grouped rather than a flat tag cloud so a reader can tell depth from breadth.
   Keep this honest: list what appears in production systems, not what has been
   touched once. MySQL is the production database across every backend; Postgres
   appears only as pgvector for blog embeddings, which is why it sits under
   Data & Messaging with that scope rather than beside MySQL. */
export interface SkillGroup {
  area: string
  skills: readonly string[]
}

export const SKILL_GROUPS: readonly SkillGroup[] = [
  {
    area: 'Backend',
    skills: ['Python', 'Django', 'Django REST Framework', 'Clean Architecture', 'DDD', 'REST APIs'],
  },
  {
    area: 'Frontend',
    skills: ['React', 'TypeScript', 'Tailwind CSS', 'Vite'],
  },
  {
    area: 'Data & Messaging',
    skills: ['MySQL', 'Redis', 'WebSockets (ASGI)', 'Background task queues', 'pgvector'],
  },
  {
    area: 'Cloud & Delivery',
    skills: ['Google Cloud', 'AWS', 'Docker', 'CI/CD', 'GitHub Actions'],
  },
  {
    area: 'AI Integration',
    skills: ['Anthropic API', 'OpenAI API', 'Embeddings & retrieval'],
  },
  {
    area: 'Leadership',
    skills: ['Architecture review', 'Vendor oversight', 'Mentoring', 'Technical writing'],
  },
] as const
