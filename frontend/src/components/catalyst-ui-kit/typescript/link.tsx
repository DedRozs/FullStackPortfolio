import * as Headless from '@headlessui/react'
import React, { forwardRef } from 'react'
import { Link as RouterLink } from 'react-router-dom'

const EXTERNAL = /^(https?:\/\/|\/\/|mailto:|tel:|#)/

export const Link = forwardRef(function Link(
  { href, ...props }: { href: string } & React.ComponentPropsWithoutRef<'a'>,
  ref: React.ForwardedRef<HTMLAnchorElement>
) {
  return (
    <Headless.DataInteractive>
      {EXTERNAL.test(href) ? (
        <a {...props} href={href} ref={ref} />
      ) : (
        <RouterLink {...props} to={href} ref={ref as React.ForwardedRef<HTMLAnchorElement>} />
      )}
    </Headless.DataInteractive>
  )
})
