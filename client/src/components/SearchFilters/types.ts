export interface FilterProps {
  // title of filter section
  title: string
  // literal options to select from (eg disease names, star ratings, etc)
  options: string[]
  // subset of options indicating what's selected by the user
  selected: string[]
  // setter to set selections
  setSelected: (values: string[]) => void
}
