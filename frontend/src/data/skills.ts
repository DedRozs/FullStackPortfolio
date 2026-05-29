export const SKILLS = [
  'Python',
  'Django',
  'React',
  'TypeScript',
  'Google Cloud',
  'Docker',
  'MySQL',
  'PostgreSQL',
  'REST APIs',
  'OpenAI',
  'CI/CD',
  'Clean Architecture',
] as const

export type Skill = (typeof SKILLS)[number]
